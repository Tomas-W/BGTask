import threading
from datetime import datetime
from typing import Callable
from math import radians, sin, cos, sqrt, atan2
import time

from service.service_utils import LocationListener, Context, LocationManager, PythonActivity, Looper
from src.utils.logger import logger

try:
    from jnius import autoclass  # type: ignore
    PythonService = autoclass('org.kivy.android.PythonService')
except ImportError:
    PythonService = None


class ServiceGpsManager:
    """
    Complete GPS manager for the service that handles all GPS operations.
    Includes utility functions and Android GPS functionality.
    """
    DEFAULT_ALERT_DISTANCE = 1000  # 1km in meters

    # Optimized polling intervals (in milliseconds)
    STATIONARY_INTERVAL = 300000   # 5 minutes when not moving  
    MOVING_INTERVAL = 30000        # 30 seconds when moving
    MIN_MOVEMENT_DISTANCE = 50     # 50 meters to consider "moving"

    def __init__(self, service_manager=None):
        # Service reference for notifications
        self.service_manager = service_manager
        
        # Location state
        self._current_lat: float | None = None
        self._current_lon: float | None = None
        self._monitoring_active: bool = False
        self._target_lat: float | None = None
        self._target_lon: float | None = None
        self._alert_distance: float = self.DEFAULT_ALERT_DISTANCE
        
        # Threading controls
        self._location_lock: threading.Lock = threading.Lock()
        self._location_event: threading.Event = threading.Event()
        
        # Android GPS components
        self._location_manager = None
        self._location_listener = None
        self._looper = None
        self._gps_enabled: bool = False
        self._last_update_time: datetime | None = None
        
        # Monitoring state
        self._last_known_location: tuple[float, float] | None = None
        self._current_interval: int = self.MOVING_INTERVAL
        
        # Initialize Android components
        self._initialize_android_gps()
        
    def _initialize_android_gps(self) -> None:
        """Initialize Android GPS components."""
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
    
    def _start_looper_thread(self) -> None:
        """Starts a thread with a prepared Looper for location updates."""
        def looper_thread():
            Looper.prepare()
            self._looper = Looper.myLooper()
            Looper.loop()
        
        self._looper_thread = threading.Thread(target=looper_thread)
        self._looper_thread.daemon = True
        self._looper_thread.start()
        
        # Wait for looper to be ready
        for _ in range(10):
            if self._looper:
                logger.info("GPS Looper thread started")
                break
            threading.Event().wait(0.1)
    
    # =============== GPS Utility Functions ===============
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in meters using Haversine formula.
        """
        R = 6371000  # Earth's radius in meters

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

    def set_target_location(self, lat: float, lon: float, alert_distance: float = None) -> None:
        """Set the target location for monitoring."""
        self._target_lat = lat
        self._target_lon = lon
        if alert_distance is not None:
            self._alert_distance = alert_distance
        logger.info(f"Target location set: {lat}, {lon} with distance {self._alert_distance}m")

    # def get_target_location(self) -> tuple[float, float, float] | None:
    #     """Get current target location and alert distance."""
    #     if self._target_lat is not None and self._target_lon is not None:
    #         return (self._target_lat, self._target_lon, self._alert_distance)
    #     return None

    def update_current_location(self, lat: float, lon: float) -> None:
        """Update the current location."""
        self._current_lat = lat
        self._current_lon = lon
        logger.info(f"Current location updated: {lat}, {lon}")

    # def get_current_location(self) -> tuple[float, float] | None:
    #     """Get the current location if available."""
    #     if self._current_lat is not None and self._current_lon is not None:
    #         return (self._current_lat, self._current_lon)
    #     return None

    def check_alert_condition(self) -> bool:
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
    
    # =============== Android GPS Functions ===============
    
    def get_location_once(self) -> tuple[float, float] | None:
        """
        Get current location once for the app.
        Returns (lat, lon) if available, None if GPS not available.
        """
        logger.info("Service: Getting one-time location update")
        
        # Ensure GPS is initialized
        if not self._ensure_gps_initialized():
            logger.warning("Service: GPS not initialized, cannot get location")
            return None
        
        # Try last known location first
        try:
            last_location = self._location_manager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
            if last_location:
                lat = last_location.getLatitude()
                lon = last_location.getLongitude()
                self.update_current_location(lat, lon)
                logger.info(f"Service: Returning last known location: {lat}, {lon}")
                return (lat, lon)
        except Exception as e:
            logger.warning(f"Error getting last known location: {e}")
        
        # No last known location available
        logger.warning("Service: No GPS location available")
        return None
    
    def start_location_monitoring(self, target_lat: float, target_lon: float, 
                                alert_distance: float = None) -> bool:
        """
        Start monitoring location for distance alerts.
        Returns True if started successfully, False otherwise.
        """
        logger.info(f"Service: Starting location monitoring for target: {target_lat}, {target_lon}")
        
        # Ensure GPS is initialized
        if not self._ensure_gps_initialized():
            logger.error("Service: GPS not initialized, cannot start monitoring")
            return False
        
        # Set target location
        self.set_target_location(target_lat, target_lon, alert_distance)
        self._monitoring_active = True
        
        # Start location updates
        success = self._start_location_service(self._on_location_update)
        if success:
            logger.info("Service: Location monitoring started successfully")
        else:
            logger.error("Service: Failed to start location monitoring")
            self._monitoring_active = False
        
        return success
    
    def stop_location_monitoring(self) -> None:
        """Stop location monitoring."""
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
        
        # Update current location
        self.update_current_location(lat, lon)
        
        # Update notification with distance
        self._update_notification_with_distance()
        
        # Check if within alert distance
        if self.check_alert_condition():
            distance = self.get_distance_to_target()
            logger.info(f"Service: Within alert distance! Distance: {distance:.2f} meters")
            self._trigger_location_alert()
            self.stop_location_monitoring()
            return
        
        # Log current distance
        distance = self.get_distance_to_target()
        if distance:
            logger.debug(f"Service: Distance to target: {distance:.2f} meters")
        
        # Adjust polling interval based on movement
        if self._last_known_location:
            movement = self.calculate_distance(
                self._last_known_location[0], self._last_known_location[1],
                lat, lon
            )
            
            new_interval = (self.MOVING_INTERVAL if movement >= self.MIN_MOVEMENT_DISTANCE 
                          else self.STATIONARY_INTERVAL)
            
            if new_interval != self._current_interval:
                logger.info(f"Service: Adjusting GPS interval to {new_interval} ms")
                self._current_interval = new_interval
                self._restart_location_updates()
        
        self._last_known_location = (lat, lon)
    
    def _trigger_location_alert(self) -> None:
        """Trigger location alert - notify the user."""
        logger.info("Service: Location alert triggered!")
        # TODO: Send notification to user
        # For now, just a mock signal to notification manager
        try:
            # Mock notification - replace with actual notification logic later
            from service.service_notification_manager import SNM
            SNM.show_notification(
                title="Location Alert",
                message="You have reached your destination!",
                sticky=False
            )
        except Exception as e:
            logger.error(f"Error sending location alert notification: {e}")
    
    def _start_location_service(self, callback: Callable[[float, float], None]) -> bool:
        """Start GPS location service."""
        try:
            # Ensure we have location manager
            if not self._location_manager:
                logger.error("Service: Location manager not initialized")
                return False
                
            # Ensure looper is ready - try to start if not available
            if not self._looper:
                logger.info("Service: Starting looper thread for GPS")
                self._start_looper_thread()
                
                # Wait a bit for looper to initialize
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
            
            self._location_listener = LocationListener(on_location)
            
            # Request location updates
            self._location_manager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                self._current_interval,  # Time between updates
                self.MIN_MOVEMENT_DISTANCE,  # Min distance for update
                self._location_listener,
                self._looper
            )
            
            self._gps_enabled = True
            logger.debug(f"Service: Started GPS with interval {self._current_interval}ms")
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
    
    def _restart_location_updates(self) -> None:
        """Restart location updates with current interval."""
        self._stop_location_service()
        self._start_location_service(self._on_location_update)
    
    def cleanup(self) -> None:
        """Cleanup when service stops."""
        logger.info("Service: Cleaning up GPS manager")
        self.stop_location_monitoring()
        if self._looper:
            self._looper.quit()
            self._looper = None

    def _update_notification_with_distance(self) -> None:
        """Update foreground notification with current distance to target."""
        if self.service_manager and self._monitoring_active:
            distance = self.get_distance_to_target()
            if distance is not None:
                # Convert to km if over 1000m
                if distance >= 1000:
                    distance_str = f"{distance / 1000:.1f} km"
                else:
                    distance_str = f"{distance:.0f} m"
                
                logger.debug(f"Service: Updating notification with distance: {distance_str}")
                # Update the service manager to refresh notification with distance
                self.service_manager.update_foreground_notification_info()

    def _ensure_gps_initialized(self) -> bool:
        """Ensure GPS is initialized, try to initialize if not done yet."""
        if self._location_manager is not None:
            return True
            
        try:
            # Try to initialize now
            if not hasattr(PythonService, 'mService') or PythonService.mService is None:
                logger.error("Service GPS: Service context still not available")
                return False
                
            service = PythonService.mService
            self._location_manager = service.getSystemService(Context.LOCATION_SERVICE)
            
            # Start looper if not already started
            if self._looper is None:
                self._start_looper_thread()
                
            logger.info("Service GPS manager initialized on demand")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPS on demand: {e}")
            return False