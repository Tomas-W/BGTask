import json
import threading
import time

from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import Callable, TYPE_CHECKING

from managers.device.device_manager import DM
from service.service_utils import LocationListener, Context, LocationManager, Looper
from src.utils.logger import logger
from src.utils.wrappers import requires_gps

from jnius import autoclass  # type: ignore
PythonService = autoclass('org.kivy.android.PythonService')

if TYPE_CHECKING:
    from service.service_manager import ServiceManager
    from service.service_audio_manager import ServiceAudioManager


class ServiceGpsManager:
    """
    Manages all GPS functionality for the Service that can:
    - Track current location
    - Calculate distance between current and target location
    - Displays distance in foreground notification
    - Trigger alerts when within alert distance
    """
    MIN_MOVEMENT_DISTANCE = 10        # 10 meters
    GPS_UPDATE_INTERVAL = 5000        # 5 seconds
    LAST_KNOWN_LOCATION_TIMEOUT = 60  # 60 seconds

    def __init__(self, service_manager: 'ServiceManager'):
        self.service_manager: 'ServiceManager' = service_manager
        self.audio_manager: 'ServiceAudioManager' = service_manager.audio_manager
        
        # Location state
        self._current_lat: float | None = None
        self._current_lon: float | None = None
        self._monitoring_active: bool = False
        self._target_lat: float | None = None
        self._target_lon: float | None = None
        self._alert_distance: float = DM.SETTINGS.DEFAULT_ALERT_DISTANCE
        self._targets: list[float] = []
        
        # Threading controls
        self._location_lock: threading.Lock = threading.Lock()
        self._location_event: threading.Event = threading.Event()
        
        # Android GPS components
        self._location_manager = None
        self._location_listener = None
        self._looper = None
        self._gps_enabled: bool = False
        self._last_update_time: datetime | None = None
        self._last_known_location: tuple[float, float] | None = None
        
        # Block multiple location requests
        self._location_request_active: bool = False

        # Tracking state
        self.gps_tracking_name: str | None = "Tanken"
        self.gps_target_id: str | None = "0"
        self.gps_alarm_name: str | None = None
        self.target_reached: bool = False
        
        self._initialize_gps()
        
    def _initialize_gps(self) -> None:
        """Get the location manager and start the looper thread."""
        try:
            # Check if service is available
            if not hasattr(PythonService, 'mService') or PythonService.mService is None:
                logger.warning("Service GPS: Service context not yet available, will initialize GPS on first use")
                return
                
            service = PythonService.mService
            self._location_manager = service.getSystemService(Context.LOCATION_SERVICE)
            self._start_looper_thread()
            logger.info("Service GPS manager initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize GPS: {e}")
    
    def _start_looper_thread(self) -> bool:
        """Starts a thread with a prepared Looper for location updates."""
        if self._looper:
            return True  # Already initialized
        
        def looper_thread():
            Looper.prepare()
            self._looper = Looper.myLooper()
            Looper.loop()
        
        self._looper_thread = threading.Thread(target=looper_thread)
        self._looper_thread.daemon = True
        self._looper_thread.start()
        
        # Wait for looper
        for _ in range(50):  # 5 seconds total
            if self._looper:
                logger.info("GPS Looper thread started")
                return True
            threading.Event().wait(0.1)
        
        logger.error("GPS Looper thread failed to start within timeout")
        return False

    def get_location_once(self) -> tuple[float, float] | None:
        """Returns users current location (lat, lon) if available."""
        # Check if any location request is already active
        if self._location_request_active:
            logger.debug("Service: Location request already active, skipping duplicate")
            return None
        
        logger.info("Service: Getting one-time location update")

        if not self._ensure_gps_initialized():
            return None
        
        # Check recent location first
        current_time = datetime.now()
        if (self._current_lat and
            self._current_lon and 
            self._last_update_time and 
            (current_time - self._last_update_time).total_seconds() < self.LAST_KNOWN_LOCATION_TIMEOUT):
            
            logger.info(f"Service: Using last known location: {self._current_lat}, {self._current_lon}")
            self._update_current_location(self._current_lat, self._current_lon)
            return (self._current_lat, self._current_lon)
        
        # Prevent duplicate requests
        self._location_request_active = True
        
        try:
            # Try warm first
            loc = self._get_location_once_warm()
            if loc:
                logger.info("Service: Got warm location")
                return loc
            return self._get_fresh_location_without_interfering()
        finally:
            self._location_request_active = False

    def _get_fresh_location_without_interfering(self) -> tuple[float, float] | None:
        """Get fresh location without interfering with existing tracking."""
        try:
            result = {"location": None, "received": False}
            
            def on_temp_location(lat: float, lon: float):
                result["location"] = (lat, lon)
                result["received"] = True
            
            temp_listener = LocationListener(on_temp_location, self)
            self._location_manager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                1000,  # 1 second
                0,     # No distance
                temp_listener,
                self._looper
            )
            
            # Wait for location (30 seconds max)
            import time
            for _ in range(300):
                if result["received"]:
                    break
                time.sleep(0.1)
            
            self._location_manager.removeUpdates(temp_listener)

            if result["received"]:
                lat, lon = result["location"]
                logger.info(f"Service: Got fresh location: {lat}, {lon}")
                self._update_current_location(lat, lon)
                return result["location"]

            else:
                logger.warning("Service: Timeout getting fresh location")
                return None
                
        except Exception as e:
            logger.error(f"Service: Error getting fresh location: {e}")
            return None

    def _start_location_service_one_time(self, callback: Callable[[float, float], None]) -> bool:
        """Start location service for one-time use - same as tracking but for single location."""
        try:
            if not self._location_manager:
                logger.error("Service: Location manager not initialized")
                return False
                
            # Ensure looper is ready
            if not self._looper:
                logger.info("Service: Starting looper thread for GPS")
                if not self._start_looper_thread():
                    logger.error("Service: Failed to start looper thread")
                    return False
                
                # Wait for looper to initialize
                for i in range(50):  # Wait up to 5 seconds
                    if self._looper:
                        break
                    time.sleep(0.1)
                
                if not self._looper:
                    logger.error("Service: Looper failed to initialize")
                    return False
            
            def on_location(lat: float, lon: float):
                with self._location_lock:
                    self._current_lat = lat
                    self._current_lon = lon
                    self._last_update_time = datetime.now()
                self._location_event.set()
                callback(lat, lon)
            
            self._location_listener = LocationListener(on_location, self)
            
            self._location_manager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                self.GPS_UPDATE_INTERVAL,
                self.MIN_MOVEMENT_DISTANCE,
                self._location_listener,
                self._looper
            )
            
            self._gps_enabled = True
            logger.debug(f"Service: Started GPS for one-time location with interval {self.GPS_UPDATE_INTERVAL}ms")
            return True
        
        except Exception as e:
            logger.error(f"Service: Error starting location service for one-time: {e}")
            return False
    
    def _pre_acquire_location(self):
        """Start background location acquisition when GPS is enabled."""
        # Skip if monitoring active or any location request active
        if not self._monitoring_active and not self._location_request_active:
            logger.info("Service: GPS enabled, pre-acquiring location in background...")
            self._location_request_active = True
            threading.Thread(target=self._background_location_acquisition, daemon=True).start()
        else:
            logger.debug("Service: Skipping background location acquisition (already active)")

    def _background_location_acquisition(self):
        """Background thread to acquire location when GPS is enabled."""
        try:
            location = self._get_fresh_location_without_interfering()
            if location:
                logger.info(f"Service: Background location acquired: {location}")
        except Exception as e:
            logger.debug(f"Background location acquisition failed: {e}")
        finally:
            self._location_request_active = False
    
    @requires_gps
    def start_location_monitoring(self) -> bool:
        """
        Start monitoring location for distance alerts.
        Returns True if started successfully, False otherwise.
        """
        data = self.get_gps_data()
        if not data:
            logger.error("Service: No GPS data found, skipping location monitoring")
            return False
        
        self.gps_tracking_name = data["name"]
        self._targets = data["targets"]
        self._alert_distance = data["alert_distance"]
        self.gps_alarm_name = data["alarm_name"]

        logger.info(f"Service: Starting location monitoring for {self.gps_tracking_name}: {self._targets}")
        
        self.target_reached = False
        if not self.set_target_location(self._targets, self._alert_distance):
            return False
        
        self._monitoring_active = True
        
        # Start location updates
        success = self._start_location_service(self._on_location_update)
        if success:
            logger.info("Service: Location monitoring started successfully")
        else:
            logger.error("Service: Failed to start location monitoring")
            self._monitoring_active = False
        
        # Try to set notification immediately
        current_location = self._get_current_location_from_file()
        if current_location:
            distance = self.calculate_distance(
                current_location[0], current_location[1],
                self._target_lat, self._target_lon
            )
            self._update_notification_with_distance(distance)
        else:
            self._update_notification_calculating_distance()
        
        return success
    
    def stop_location_monitoring(self) -> None:
        """Stop location monitoring and clean up notifications."""
        logger.info("Service: Stopping location monitoring")
        self._monitoring_active = False
        self._stop_location_service()
        self._target_lat = None
        self._target_lon = None
        self._last_known_location = None
    
    def _on_location_update(self, lat: float, lon: float) -> None:
        """Handle location updates during monitoring."""
        if not self._monitoring_active:
            return
        
        distance = self.get_distance_to_target()
        self._update_current_location(lat, lon)
        self._update_notification_with_distance(distance)
        
        # Check if within alert distance
        if self._check_alert_condition() and not self.target_reached:
            logger.info(f"Service: Within alert distance! Distance: {distance:.2f} meters")
            self._trigger_location_alert()
            self.audio_manager.audio_player.play(self.audio_manager.get_alarm_path(self.gps_alarm_name))
            self.target_reached = True
            return
        
        # Log current distance
        if distance:
            logger.debug(f"Service: Distance to target: {distance:.2f} meters")
        
        self._last_known_location = (lat, lon)
    
    def _trigger_location_alert(self) -> None:
        """Trigger location alert - notify the user."""
        logger.info("Service: Location alert triggered!")
        
        if self.service_manager:
            notification_manager = self.service_manager.notification_manager
            
            # Show alert notification
            notification_manager.show_gps_alert_notification(
                target_name=self.gps_tracking_name,
                target_id=self.gps_target_id,
                has_next_target=False  # Set based on target queue
            )
    
    def _start_location_service(self, callback: Callable[[float, float], None]) -> bool:
        """Start GPS location service."""
        try:
            if not self._location_manager:
                logger.error("Service: Location manager not initialized")
                return False
                
            # Ensure looper
            if not self._looper:
                logger.info("Service: Starting looper thread for GPS")
                if not self._start_looper_thread():
                    logger.error("Service: Failed to start looper thread")
                    return False
                
                # Wait for looper
                for _ in range(50):  # Wait up to 5 seconds
                    if self._looper:
                        break
                    time.sleep(0.1)
                
                if not self._looper:
                    logger.error("Service: Looper failed to initialize")
                    return False
            
            def on_location(lat: float, lon: float):
                with self._location_lock:
                    self._current_lat = lat
                    self._current_lon = lon
                    self._last_update_time = datetime.now()
                self._location_event.set()
                callback(lat, lon)
            
            self._location_listener = LocationListener(on_location, self)
            
            # Request location updates with fixed interval
            self._location_manager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                self.GPS_UPDATE_INTERVAL,
                self.MIN_MOVEMENT_DISTANCE,
                self._location_listener,
                self._looper
            )
            
            self._gps_enabled = True
            logger.debug(f"Service: Started GPS with interval {self.GPS_UPDATE_INTERVAL}ms")
            return True
        
        except Exception as e:
            logger.error(f"Service: Error starting location service: {e}")
            return False
    
    def _stop_location_service(self) -> None:
        """Stop GPS location service."""
        try:
            if self._location_listener and self._location_manager:
                self._location_manager.removeUpdates(self._location_listener)
                self._location_listener = None
            self._gps_enabled = False
            logger.debug("Service: Stopped GPS location service")
        except Exception as e:
            logger.error(f"Service: Error stopping location service: {e}")
    
    def cleanup(self) -> None:
        """Cleanup when service stops."""
        logger.info("Service: Cleaning up GPS manager")
        self.stop_location_monitoring()
        if self._looper:
            self._looper.quit()
            self._looper = None

    def _update_notification_with_distance(self, distance: float) -> None:
        """Update notification with current distance to target."""
        if self.service_manager and self._monitoring_active:
            # distance = self.get_distance_to_target()
            if distance is not None:
                notification_manager = self.service_manager.notification_manager
                notification_manager.show_gps_tracking_notification(
                    distance=distance,
                    target_name=self.gps_tracking_name,
                    target_id=self.gps_target_id,
                    has_next_target=False
                )
    
    def _update_notification_calculating_distance(self) -> None:
        """Update notification with calculating distance."""
        if self.service_manager and self._monitoring_active:
            notification_manager = self.service_manager.notification_manager
            notification_manager.show_gps_tracking_notification(
                distance=-1,  # shown as "calculating..."
                target_name=self.gps_tracking_name,
                target_id=self.gps_target_id,
                has_next_target=False
            )

    def _ensure_gps_initialized(self) -> bool:
        """Ensure GPS is initialized, try to initialize if not done yet."""
        if self._location_manager is not None:
            return True
            
        try:
            if not hasattr(PythonService, 'mService') or PythonService.mService is None:
                logger.error("Service GPS: Service context still not available")
                return False
                
            service = PythonService.mService
            self._location_manager = service.getSystemService(Context.LOCATION_SERVICE)
            
            if self._looper is None:
                self._start_looper_thread()
                
            logger.info("Service GPS manager initialized on demand")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPS on demand: {e}")
            return False
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in meters using Haversine formula.
        """
        R = 6371000  # Earth's radius

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def is_within_alert_distance(self, current_lat: float, current_lon: float, 
                                target_lat: float, target_lon: float, 
                                alert_distance: float) -> bool:
        """Check if current location is within alert distance of target."""
        distance = self.calculate_distance(current_lat, current_lon, target_lat, target_lon)
        return distance <= alert_distance

    def set_target_location(self, targets: list[float], alert_distance: float = None) -> None:
        """
        Set the target_lat, target_lon and alert_distance for monitoring.
        Retuns False if no valid targets are provided.
        """
        self._targets = targets
        
        # Set first target as active target
        if not targets or len(targets) == 0 or len(targets) % 2 != 0:
            logger.error("No valid target coordinates provided")
            return False
        
        self._target_lat, self._target_lon = targets[0], targets[1]
        if alert_distance > DM.SETTINGS.DEFAULT_ALERT_DISTANCE:
            self._alert_distance = alert_distance
        
        logger.info(f"Target location set: {len(targets)} targets with distance {self._alert_distance}m")
        return True

    def _update_current_location(self, lat: float, lon: float) -> None:
        """Update the current location."""
        self._current_lat = lat
        self._current_lon = lon
        self._last_update_time = datetime.now()
        self.save_location_to_file(lat, lon)
        logger.info(f"Current location updated: {lat}, {lon}")

    def _check_alert_condition(self) -> bool:
        """Check if current location triggers alert condition."""
        if (self._current_lat is None or self._current_lon is None or 
            self._target_lat is None or self._target_lon is None):
            return False
        
        return self.is_within_alert_distance(
            self._current_lat, self._current_lon,
            self._target_lat, self._target_lon,
            self._alert_distance
        )

    def get_distance_to_target(self) -> float | None:
        """Get current distance to target in meters."""
        if (self._current_lat is None or self._current_lon is None or 
            self._target_lat is None or self._target_lon is None):
            return None
        
        return self.calculate_distance(
            self._current_lat, self._current_lon,
            self._target_lat, self._target_lon
        )
    
    def get_gps_data(self) -> dict[str, list[dict[str, float]] | float] | None:
        """Returns GPS data dict from file."""
        try:
            with open(DM.PATH.GPS_FILE, "r") as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"Error getting GPS targets: {e}")
            return None
    
    def _get_current_location_from_file(self) -> tuple[float, float] | None:
        """Returns current location from file."""
        try:
            with open(DM.PATH.GPS_FILE, "r") as f:
                data = json.load(f)
                if data and "current_location" in data:
                    return tuple(data["current_location"])
                return None
        
        except Exception as e:
            logger.error(f"Error getting current location: {e}")
            return None
    
    def save_location_to_file(self, lat: float, lon: float) -> None:
        """Overwrites current location in file."""
        try:
            existing_data = {}
            try:
                with open(DM.PATH.GPS_FILE, "r") as f:
                    existing_data = json.load(f)
            
            except FileNotFoundError:
                pass
            
            existing_data["current_location"] = [lat, lon]
            
            with open(DM.PATH.GPS_FILE, "w") as f:
                json.dump(existing_data, f, indent=4)
            logger.debug(f"Updated current location: {lat}, {lon}")
        
        except Exception as e:
            logger.error(f"Error saving current location: {e}")
    
    def _save_targets_and_distance(self, targets: list[float], alert_distance: float) -> None:
        """Overwrites GPS targets and alert distance in file."""
        try:
            existing_data = {}
            try:
                with open(DM.PATH.GPS_FILE, "r") as f:
                    existing_data = json.load(f)
            
            except FileNotFoundError:
                pass
            
            existing_data.update({
                "targets": targets,
                "alert_distance": alert_distance
            })
            
            with open(DM.PATH.GPS_FILE, "w") as f:
                json.dump(existing_data, f, indent=4)
            logger.info(f"Saved GPS targets: {targets}, alert_distance: {alert_distance}")
        
        except Exception as e:
            logger.error(f"Error saving GPS targets: {e}")
    
    def _reset_gps_file(self) -> None:
        """Resets GPS file to default values."""
        try:
            with open(DM.PATH.GPS_FILE, "w") as f:
                json.dump({
                    "name": None,
                    "targets": None,
                    "alert_distance": 0,
                    "alarm_name": None
                }, f, indent=4)
            logger.info("Reset GPS file")
        
        except Exception as e:
            logger.error(f"Error resetting GPS file: {e}")

    def _get_location_once_warm(self) -> tuple[float, float] | None:
        """Starts updates on available providers and stops after first fix."""
        try:
            if not self._ensure_gps_initialized():
                return None
            if not self._looper and not self._start_looper_thread():
                return None

            result = {"loc": None}
            event = threading.Event()

            def on_temp_location(lat: float, lon: float):
                # self._update_current_location(lat, lon)
                result["loc"] = (lat, lon)
                event.set()

            listeners = []
            gps_enabled = False
            net_enabled = False
            try:
                gps_enabled = self._location_manager.isProviderEnabled(LocationManager.GPS_PROVIDER)
            except Exception:
                pass
            try:
                net_enabled = self._location_manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
            except Exception:
                pass

            if not gps_enabled and not net_enabled:
                logger.warning("Service: No provider enabled for one-shot")
                return None

            if gps_enabled:
                listeners.append(("gps", LocationListener(on_temp_location, self)))
                self._location_manager.requestLocationUpdates(
                    LocationManager.GPS_PROVIDER, 0, 0.0, listeners[-1][1], self._looper
                )
            if net_enabled:
                listeners.append(("net", LocationListener(on_temp_location, self)))
                self._location_manager.requestLocationUpdates(
                    LocationManager.NETWORK_PROVIDER, 0, 0.0, listeners[-1][1], self._looper
                )

            event.wait(10.0)
            return result["loc"]

        except Exception as e:
            logger.error(f"Service: Error in warm one-shot: {e}")
            return None
        finally:
            try:
                for _, l in locals().get("listeners", []):
                    self._location_manager.removeUpdates(l)
            except Exception:
                pass
