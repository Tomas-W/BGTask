from managers.device.device_manager import DM
from src.utils.wrappers import android_only_class
from src.utils.logger import logger


try:
    from jnius import autoclass        # type: ignore
    from android.permissions import (  # type: ignore
        Permission,
        check_permission,
        request_permissions
    )
except Exception as e:
    pass


@android_only_class(except_methods=["__init__"])
class PermissionManager:
    """
    Manages Permissions for the App and Service.
    """
    def __init__(self):
        # Need attributes even if not Android
        if DM.is_android:
            # Basic permissions, shared methods
            self.POST_NOTIFICATIONS = Permission.POST_NOTIFICATIONS
            self.RECORD_AUDIO = Permission.RECORD_AUDIO
            self.SET_WALLPAPER = Permission.SET_WALLPAPER
        else:
            self.POST_NOTIFICATIONS = "POST_NOTIFICATIONS"
            self.RECORD_AUDIO = "RECORD_AUDIO"
            self.SET_WALLPAPER = "SET_WALLPAPER"	

        # Special case permissions, individual methods
        self.REQUEST_SCHEDULE_EXACT_ALARM: str = "REQUEST_SCHEDULE_EXACT_ALARM"
        self.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS: str = "ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"

    def validate_permission(self, permission: str) -> bool:
        """
        Returns True if the App has the given permission.
        If not, requests permission and returns False.
        """
        if permission == self.REQUEST_SCHEDULE_EXACT_ALARM:
            self.request_exact_alarm_permission()
            return False
        
        elif permission == self.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS:
            self.request_battery_exemption()
            return False

        try:
            if check_permission(permission):
                logger.trace(f"{permission} already granted")
                return True
        
        except Exception as e:
            logger.error(f"Error checking permission: {permission}: {e}")
            return False
        
        try:
            request_permissions([permission],
                                 self._permission_callback)
            logger.trace(f"{permission} requested")
            return False
        
        except Exception as e:
            logger.error(f"Error requesting permission: {permission}: {e}")
            return False
    
    def _permission_callback(self, permissions: list[str], results: list[bool]) -> None:
        """Callback for permission requests."""
        if not permissions or not results:
            logger.warning(f"Permission callback received empty permissions or results: {permissions=}, {results=}")
            return
        
        permission = permissions[0]
        if all(results):
            logger.trace(f"{permission} granted")
        else:
            logger.warning(f"{permission} denied")
    
    def _check_battery_exemption(self) -> bool:
        """Returns whether the app is granted ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS."""
        try:
            Context = autoclass("android.content.Context")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            
            context = PythonActivity.mActivity
            package_name = context.getPackageName()
            power_manager = context.getSystemService(Context.POWER_SERVICE)
            result = power_manager.isIgnoringBatteryOptimizations(package_name)
            return result
        
        except Exception as e:
            logger.error(f"Error checking permission: ACTION_IGNORE_BATTERY_OPTIMIZATIONS: {e}")
            return False
    
    def request_battery_exemption(self) -> None:
        """Opens system settings to request ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS."""
        try:
            # Check if already granted
            if self._check_battery_exemption():
                logger.trace(f"ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS permission already granted")
                return
            
            Intent = autoclass("android.content.Intent")
            Settings = autoclass("android.provider.Settings")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Uri = autoclass("android.net.Uri")
            
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            package_name = context.getPackageName()

            intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            intent.setData(Uri.parse(f"package:{package_name}"))
            activity.startActivity(intent)
            logger.debug("ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS permission requested")
        
        except Exception as e:
            logger.error(f"Error requesting permission ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS: {e}")
    
    def _check_exact_alarm_permission(self) -> bool:
        """Returns whether the app has REQUEST_SCHEDULE_EXACT_ALARM permission."""
        if not self._is_android_12_or_higher():
            return True
        
        try:
            Context = autoclass("android.content.Context")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            
            context = PythonActivity.mActivity
            alarm_manager = context.getSystemService(Context.ALARM_SERVICE)
            
            has_permission = alarm_manager.canScheduleExactAlarms()
            result = "already granted" if has_permission else "not yet granted"
            logger.trace(f"REQUEST_SCHEDULE_EXACT_ALARM permission check: {result}.")
            return has_permission
        
        except Exception as e:
            logger.error(f"Error checking permission: REQUEST_SCHEDULE_EXACT_ALARM: {e}")
            return False
    
    def request_exact_alarm_permission(self) -> None:
        """Opens system settings to request REQUEST_SCHEDULE_EXACT_ALARM permission."""
        if not self._is_android_12_or_higher():
            return
        
        try:
            # Check if already granted
            if self._check_exact_alarm_permission():
                return
            
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Uri = autoclass("android.net.Uri")
            
            activity = PythonActivity.mActivity
            package_name = activity.getPackageName()

            intent = Intent("android.settings.REQUEST_SCHEDULE_EXACT_ALARM")
            intent.setData(Uri.parse(f"package:{package_name}"))
            activity.startActivity(intent)
            logger.debug("REQUEST_SCHEDULE_EXACT_ALARM permission requested")
        
        except Exception as e:
            logger.error(f"Error requesting exact alarm permission: {e}")
    
    def _is_android_12_or_higher(self) -> bool:
        """Returns whether the device is running Android 12 or higher."""
        try:
            BuildVersion = autoclass("android.os.Build$VERSION")
            return BuildVersion.SDK_INT >= 31  # Android 12 is API level 31
        
        except Exception as e:
            logger.error(f"Error checking Android version: {e}")
            return False


PM = PermissionManager()
