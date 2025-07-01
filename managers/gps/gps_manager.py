# import threading
# from datetime import datetime
# from typing import Callable
# from math import radians, sin, cos, sqrt, atan2

# from src.utils.wrappers import android_only_class
# from src.utils.logger import logger

# LocationListener = None
# Context = None
# LocationManager = None
# PythonActivity = None
# Looper = None

# try:
#     from jnius import autoclass, PythonJavaClass, java_method  # type: ignore
#     Context = autoclass('android.content.Context')
#     LocationManager = autoclass('android.location.LocationManager')
#     PythonActivity = autoclass('org.kivy.android.PythonActivity')
#     Looper = autoclass('android.os.Looper')

#     class _LocationListener(PythonJavaClass):
#         """Android location listener implementation."""
#         __javainterfaces__ = ['android/location/LocationListener']
        
#         def __init__(self, callback):
#             super().__init__()
#             self.callback = callback

#         @java_method('(Landroid/location/Location;)V')
#         def onLocationChanged(self, location):
#             """Called when location changes (old API)."""
#             if location:
#                 self.callback(
#                     location.getLatitude(),
#                     location.getLongitude()
#                 )
        
#         @java_method('(Ljava/util/List;)V')
#         def onLocationChanged(self, locations):
#             """Called when location changes (new API)."""
#             try:
#                 if locations and locations.size() > 0:
#                     location = locations.get(locations.size() - 1)  # Most recent
#                     self.callback(
#                         location.getLatitude(),
#                         location.getLongitude()
#                     )
#             except Exception as e:
#                 logger.error(f"Error handling location list update: {e}")
        
#         @java_method('(Ljava/lang/String;)V')
#         def onProviderEnabled(self, provider):
#             """Called when provider is enabled."""
#             logger.debug(f"Location provider enabled: {provider}")

#         @java_method('(Ljava/lang/String;)V')
#         def onProviderDisabled(self, provider):
#             """Called when provider is disabled."""
#             logger.warning(f"Location provider disabled: {provider}")
        
#         @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
#         def onStatusChanged(self, provider, status, extras):
#             """Called when provider status changes."""
#             pass
    
#     LocationListener = _LocationListener

# except Exception as e:
#     pass


# @android_only_class()
# class GPSManager:
#     """
#     Manages GPS throughout the App and Service.
#     Optimized for distance-based monitoring with battery efficiency.
#     """
    
#     DEFAULT_LAT = 51.543368
#     DEFAULT_LON = 3.603933

#     # Optimized polling intervals
#     LOCATION_TIMEOUT = 10         # 10 seconds timeout for location updates
#     STATIONARY_INTERVAL = 60000   # 1 minute when not moving
#     MOVING_INTERVAL = 10000       # 10 seconds when moving
#     MIN_MOVEMENT_DISTANCE = 50    # 50 meters to consider "moving"
#     LOCATION_ACCURACY = 100       # 100 meters accuracy
    
#     def __init__(self):
#         self._current_lat: float | None = None
#         self._current_lon: float | None = None
#         self._last_update_time: datetime | None = None
        
#         # Threading controls
#         self._location_lock: threading.Lock = threading.Lock()
#         self._location_event: threading.Event = threading.Event()
        
#         # Location manager
#         activity = PythonActivity.mActivity
#         self._location_manager = activity.getSystemService(Context.LOCATION_SERVICE)
#         self._location_listener = None
#         self._looper = None
#         self._gps_enabled: bool = False
        
#         # Start looper thread
#         self._start_looper_thread()
        
#         # Monitoring state
#         self._monitoring_active: bool = False
#         self._target_lat: float | None = None
#         self._target_lon: float | None = None
#         self._alert_distance: float = GPSManager.DEFAULT_ALERT_DISTANCE
#         self._alert_callback: Callable[[], None] | None = None
#         self._last_known_location: tuple[float, float] | None = None
#         self._current_interval: int = GPSManager.MOVING_INTERVAL
    
#     def _start_looper_thread(self):
#         """Starts a thread with a prepared Looper for location updates."""
#         def looper_thread():
#             Looper.prepare()
#             self._looper = Looper.myLooper()
#             Looper.loop()
        
#         self._looper_thread = threading.Thread(target=looper_thread)
#         self._looper_thread.daemon = True
#         self._looper_thread.start()
        
#         # Wait
#         for _ in range(10):
#             if self._looper:
#                 logger.info("Looper thread started")
#                 break
#             threading.Event().wait(0.1)
#         logger.info("Looper thread started ONLY IF THIS IS 2ND MESSAGE")
    
#     def track_current_location(self, callback: Callable[[float, float], None]) -> None:
#         """
#         Tracks current location coordinates asynchronously.
#         Calls the callback with (latitude, longitude) when location is available.
#         """
#         if self._have_recent_location():
#             callback(self._current_lat, self._current_lon)
#             return
            
#         if not self._gps_enabled:
#             self._start_location_service(callback)
        
#         # Start thread to wait for location
#         thread = threading.Thread(target=self._wait_for_location, args=(callback,))
#         thread.daemon = True
#         thread.start()
    
#     def _have_recent_location(self, max_age_seconds: float = 30.0) -> bool:
#         """Checks if we have a recent location fix."""
#         with self._location_lock:
#             if (self._current_lat is None or 
#                 self._current_lon is None or 
#                 self._last_update_time is None):
#                 return False
            
#             age = (datetime.now() - self._last_update_time).total_seconds()
#             return age <= max_age_seconds
    
#     def _wait_for_location(self, callback: Callable[[float, float], None]) -> None:
#         """Waits for location update and calls callback when received."""
#         # Try to get last known location first
#         try:
#             last_location = self._location_manager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
#             if last_location:
#                 with self._location_lock:
#                     self._current_lat = last_location.getLatitude()
#                     self._current_lon = last_location.getLongitude()
#                     self._last_update_time = datetime.now()
#                 callback(self._current_lat, self._current_lon)
#                 return
#         except Exception as e:
#             logger.warning(f"Error getting last known location: {e}")
        
#         # Wait for new location
#         self._location_event.wait(GPSManager.LOCATION_TIMEOUT)
        
#         with self._location_lock:
#             if self._current_lat is not None and self._current_lon is not None:
#                 callback(self._current_lat, self._current_lon)
#             else:
#                 logger.warning("Location timeout, using default coordinates")
#                 callback(self.DEFAULT_LAT, self.DEFAULT_LON)
    
#     def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#         """
#         Calculate distance between two points in meters using Haversine formula.
#         """
#         R = 6371000

#         lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1

#         a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
#         c = 2 * atan2(sqrt(a), sqrt(1-a))
#         return R * c

#     def start_monitoring(self, target_lat: float, target_lon: float, 
#                         alert_callback: Callable[[], None]) -> None:
#         """
#         Start monitoring distance to target location.
#         Calls alert_callback when within alert_distance.
#         """
#         logger.info(f"Starting monitoring with target: {target_lat}, {target_lon}")
#         self._target_lat = target_lat
#         self._target_lon = target_lon
#         self._alert_callback = alert_callback
#         self._monitoring_active = True

#         def location_callback(lat: float, lon: float) -> None:
#             if not self._monitoring_active:
#                 return
            
#             distance = self.calculate_distance(lat, lon, self._target_lat, self._target_lon)
#             logger.info(f"Distance: {distance} meters")

#             # Check if within alert distance
#             if distance <= self._alert_distance:
#                 logger.info(f"Within alert distance: {distance} meters")
#                 self._alert_callback()
#                 self.stop_monitoring()
#                 return
#             else:
#                 logger.info(f"Distance outside alert distance: {distance} meters")

#             # Adjust polling interval based on movement
#             if self._last_known_location:
#                 movement = self.calculate_distance(
#                     self._last_known_location[0], self._last_known_location[1],
#                     lat, lon
#                 )
                
#                 new_interval = (self.MOVING_INTERVAL if movement >= self.MIN_MOVEMENT_DISTANCE 
#                               else self.STATIONARY_INTERVAL)
                
#                 if new_interval != self._current_interval:
#                     logger.info(f"Restartig with new interval: {new_interval} ms")
#                     self._current_interval = new_interval
#                     # Restart location updates with new interval
#                     self._restart_location_updates(location_callback)

#             self._last_known_location = (lat, lon)

#         logger.info(f"Starting initial location updates with interval: {self._current_interval} ms")
#         # Start location updates
#         self._start_location_service(location_callback)

#     def _restart_location_updates(self, callback: Callable[[float, float], None]) -> None:
#         """Restart location updates with current interval."""
#         self._stop_location_service()
#         self._start_location_service(callback)

#     def stop_monitoring(self) -> None:
#         """Stop monitoring location."""
#         self._monitoring_active = False
#         self._target_lat = None
#         self._target_lon = None
#         self._alert_callback = None
#         self._last_known_location = None
#         self.stop()

#     def _start_location_service(self, callback: Callable[[float, float], None]) -> None:
#         """Starts the GPS location service with optimized parameters."""
#         try:
#             if not self._looper:
#                 logger.error("Looper not initialized")
#                 return
            
#             def on_location(lat, lon):
#                 with self._location_lock:
#                     self._current_lat = lat
#                     self._current_lon = lon
#                     self._last_update_time = datetime.now()
#                 self._location_event.set()
#                 callback(lat, lon)
#                 logger.debug(f"Location updated: {lat}, {lon}")
            
#             self._location_listener = LocationListener(on_location)
            
#             # Request location updates with optimized parameters
#             self._location_manager.requestLocationUpdates(
#                 LocationManager.GPS_PROVIDER,
#                 self._current_interval,  # Time between updates
#                 self.MIN_MOVEMENT_DISTANCE,  # Min distance for update
#                 self._location_listener,
#                 self._looper
#             )
            
#             self._gps_enabled = True
#             logger.debug(f"Started GPS location service with interval {self._current_interval}ms")
        
#         except Exception as e:
#             logger.error(f"Error starting location service: {e}")
    
#     def _stop_location_service(self) -> None:
#         """Stops the GPS location service."""
#         try:
#             if self._location_listener:
#                 self._location_manager.removeUpdates(self._location_listener)
#             self._gps_enabled = False
            
#             # Quit looper
#             # if self._looper:
#             #     self._looper.quit()
#             #     self._looper = None
            
#             logger.debug("Stopped GPS location service")
        
#         except Exception as e:
#             logger.error(f"Error stopping location service: {e}")
    
#     def _stop_looper(self) -> None:
#         """Stops the looper thread."""
#         if self._looper:
#             self._looper.quit()
#             self._looper = None
    
#     def stop(self) -> None:
#         """Stops GPS and cleans up."""
#         self._stop_location_service()
#         self._location_event.set()

#     def get_current_location(self, callback: Callable[[float, float], None]) -> None:
#         """
#         Gets current location coordinates once and then stops.
#         Calls the callback with (latitude, longitude) when location is available.
#         """
#         logger.debug("Getting one-time location update")
        
#         def one_time_callback(lat: float, lon: float) -> None:
#             callback(lat, lon)
#             self._stop_location_service()
#             logger.debug("One-time location received, stopped location service")
        
#         # Try last known location first
#         try:
#             last_location = self._location_manager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
#             if last_location:
#                 one_time_callback(last_location.getLatitude(), last_location.getLongitude())
#                 return
#         except Exception as e:
#             logger.warning(f"Error getting last known location: {e}")
        
#         # If no last location, request single update
#         try:
#             if not self._looper:
#                 logger.error("Looper not initialized")
#                 return
            
#             self._location_listener = LocationListener(one_time_callback)
#             self._location_manager.requestLocationUpdates(
#                 LocationManager.GPS_PROVIDER,
#                 0,  # minTime
#                 0,  # minDistance
#                 self._location_listener,
#                 self._looper
#             )
            
#             self._gps_enabled = True
#             logger.debug("Requested one-time location update")
            
#             # Set timeout if no location
#             def timeout():
#                 if self._gps_enabled:
#                     logger.warning("Location timeout, using default coordinates")
#                     one_time_callback(self.DEFAULT_LAT, self.DEFAULT_LON)
            
#             from kivy.clock import Clock
#             Clock.schedule_once(lambda dt: timeout(), 10)
            
#         except Exception as e:
#             logger.error(f"Error requesting one-time location: {e}")
#             callback(self.DEFAULT_LAT, self.DEFAULT_LON)
