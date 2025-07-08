from datetime import datetime, timedelta
from typing import Any, Callable, TYPE_CHECKING

from jnius import autoclass, PythonJavaClass, java_method  # type: ignore
from managers.device.device_manager import DM

from src.utils.logger import logger

# Android classes for GPS
Context = autoclass('android.content.Context')
LocationManager = autoclass('android.location.LocationManager')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Looper = autoclass('android.os.Looper')

if TYPE_CHECKING:
    from service.service_gps_manager import ServiceGpsManager


class LocationListener(PythonJavaClass):
    """Android location listener implementation for service use."""
    __javainterfaces__ = ['android/location/LocationListener']
    
    def __init__(self, callback: Callable[[float, float], None], gps_manager: 'ServiceGpsManager'):
        super().__init__()
        self.callback = callback
        self.gps_manager = gps_manager

    @java_method('(Landroid/location/Location;)V')
    def onLocationChanged(self, location):
        """Called when location changes (old API)."""
        if location:
            self.callback(
                location.getLatitude(),
                location.getLongitude()
            )
    
    @java_method('(Ljava/util/List;)V')
    def onLocationChanged(self, locations):
        """Called when location changes (new API)."""
        try:
            if locations and locations.size() > 0:
                location = locations.get(locations.size() - 1)  # Most recent
                self.callback(
                    location.getLatitude(),
                    location.getLongitude()
                )
        except Exception as e:
            logger.error(f"Error handling location list update: {e}")
    
    @java_method('(Ljava/lang/String;)V')
    def onProviderEnabled(self, provider):
        """Called when GPS provider is enabled."""
        logger.info(f"Location provider enabled: {provider}")
        if provider == "gps" and hasattr(self, 'gps_manager'):
            # Pre-start location acquisition when GPS is enabled
            self.gps_manager._pre_acquire_location()
    
    @java_method('(Ljava/lang/String;)V')
    def onProviderDisabled(self, provider):
        """Called when GPS provider is disabled."""
        logger.info(f"Location provider disabled: {provider}")
    
    @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
    def onStatusChanged(self, provider, status, extras):
        """Called when provider status changes."""
        pass


def get_service_timestamp(task: Any) -> str:
    """
    Returns the timestamp in the format of the ServiceNotification
    This includes the snooze time
    """
    try:
        timestamp = task.timestamp
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        if timestamp.date() == today:
            return f"Today @ {timestamp.strftime(DM.DATE.TASK_TIME)}"
        
        elif timestamp.date() == tomorrow:
            return f"Tomorrow @ {timestamp.strftime(DM.DATE.TASK_TIME)}"
        
        else:
            return f"{timestamp.strftime(DM.DATE.MONTH_DAY)} @ {timestamp.strftime(DM.DATE.TASK_TIME)}"
    
    except Exception as e:
        logger.error(f"Error getting service timestamp: {e}")
        return "00:00:00"
