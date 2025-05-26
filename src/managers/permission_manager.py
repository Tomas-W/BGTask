from managers.device.device_manager import DM
from src.utils.logger import logger


class PermissionManager:
    """
    Manages permissions for the app.
    """
    def __init__(self):
        self.has_recording_permission: bool = self._check_recording_permission()
        self.has_wallpaper_permission: bool = self._check_wallpaper_permission()

    def _check_recording_permission(self) -> bool:
        """
        Returns whether Android RECORD_AUDIO permission is granted.
        Always returns True for non-Android devices.
        """
        if not DM.is_android:
            return True
        
        try:
            from android.permissions import check_permission, Permission  # type: ignore
            return check_permission(Permission.RECORD_AUDIO)
        
        except Exception as e:
            logger.error(f"_check_recording_permission Error: {e}")
            return False
    
    def request_android_recording_permissions(self) -> None:
        """Displays a dialog to request Android RECORD_AUDIO permissions."""
        if not DM.is_android:
            return
        
        logger.debug("Requesting Android recording permissions")
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.RECORD_AUDIO],
                self._recording_permission_callback
            )

        except Exception as e:
            logger.error(f"_request_android_recording_permissions Error: {e}")
    
    def _recording_permission_callback(self, permissions: list[str], results: list[bool]) -> None:
        """
        Sets has_recording_permission based on the results of the permission request.
        """
        if all(results):
            logger.debug(f"Permissions {permissions} granted")
            self.has_recording_permission = True
        else:
            logger.debug(f"Permissions {permissions} denied")
            self.has_recording_permission = False
    
    def _check_wallpaper_permission(self) -> bool:
        """Returns whether Android SET_WALLPAPER permission is granted."""
        if not DM.is_android:
            return True
        
        try:
            from android.permissions import check_permission, Permission  # type: ignore
            return check_permission(Permission.SET_WALLPAPER)
        
        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
            return False
    
    def request_android_wallpaper_permissions(self) -> None:
        """Displays a dialog to request Android SET_WALLPAPER permissions."""
        if not DM.is_android:
            return
        
        logger.debug("Requesting Android wallpaper permissions")
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.SET_WALLPAPER],
                self._wallpaper_permission_callback
            )
        
        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
    
    def _wallpaper_permission_callback(self, permissions: list[str], results: list[bool]) -> None:
        """Sets has_wallpaper_permission based on the results of the permission request."""
        if all(results):
            logger.debug(f"Permissions {permissions} granted")
            self.has_wallpaper_permission = True
        else:
            logger.debug(f"Permissions {permissions} denied")
            self.has_wallpaper_permission = False


PM = PermissionManager()
