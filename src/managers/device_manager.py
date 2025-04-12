import os
import time

from src.utils.logger import logger


from src.settings import PLATFORM


class DeviceManager:
    """
    Manages device-related operations.
    """
    def __init__(self):
        self.is_android: bool = self._device_is_android()
        self.is_windows: bool = not self.is_android

        self.has_recording_permission: bool = self.check_recording_permission()
        self.has_wallpaper_permission: bool = self.check_wallpaper_permission()

    def _device_is_android(self):
        """Returns whether the app is running on Android."""
        from kivy.utils import platform
        return platform == PLATFORM.ANDROID
    
    def get_storage_path(self, directory):
        """Returns the app-specific storage path for the given directory."""
        if self.is_android:
            return os.path.join(os.environ['ANDROID_PRIVATE'], directory)
        else:
            return os.path.join(directory)
    
    def validate_dir(self, dir_path) -> bool:
        """Validate and create a directory if it doesn't exist."""
        if not os.path.isdir(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
                return True
            
            except PermissionError:
                logger.error(f"Permission denied: Cannot create directory {dir_path}. Check app permissions.")
                return False
            except FileNotFoundError:
                logger.error(f"Invalid path: {dir_path} does not exist.")
                return False
            except OSError as e:
                logger.error(f"OS error while creating {dir_path}: {e}")
                return False

    def validate_file(self, file_path: str) -> bool:
        """Validate and create a file if it doesn't exist."""
        if not os.path.isfile(file_path):
            try:
                with open(file_path, "r") as f:
                    return True

            except PermissionError:
                logger.error(f"Permission denied: Cannot create file {file_path}. Check app permissions.")
                return False
            except FileNotFoundError:
                logger.error(f"Invalid path: {file_path} does not exist.")
                return False
            except OSError as e:
                logger.error(f"OS error while creating {file_path}: {e}")
                return False

    def check_recording_permission(self) -> bool:
        """Returns whether Android RECORD_AUDIO permission is granted."""
        if not self.is_android:
            return True
        
        try:
            from android.permissions import check_permission, Permission  # type: ignore
            return check_permission(Permission.RECORD_AUDIO)
        
        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
            return False
    
    def request_android_recording_permissions(self) -> None:
        """Displays a dialog to request Android RECORD_AUDIO permissions."""
        if not self.is_android:
            return
        
        logger.debug("Requesting Android recording permissions")
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.RECORD_AUDIO],
                self.recording_permission_callback
            )

        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
    
    def recording_permission_callback(self, permissions: list[str], results: list[bool]) -> None:
        """
        Sets has_recording_permission based on the results of the permission request.
        """
        if all(results):
            logger.debug(f"Permissions {permissions} granted")
            self.has_recording_permission = True
        else:
            logger.debug(f"Permissions {permissions} denied")
            self.has_recording_permission = False
    
    def check_wallpaper_permission(self) -> bool:
        """Returns whether Android SET_WALLPAPER permission is granted."""
        if not self.is_android:
            return True
        
        try:
            from android.permissions import check_permission, Permission  # type: ignore
            return check_permission(Permission.SET_WALLPAPER)
        
        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
            return False
    
    def request_android_wallpaper_permissions(self) -> None:
        """Displays a dialog to request Android SET_WALLPAPER permissions."""
        if not self.is_android:
            return
        
        logger.debug("Requesting Android wallpaper permissions")
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.SET_WALLPAPER],
                self.wallpaper_permission_callback
            )

        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
    
    def wallpaper_permission_callback(self, permissions: list[str], results: list[bool]) -> None:
        """Sets has_wallpaper_permission based on the results of the permission request."""
        if all(results):
            logger.debug(f"Permissions {permissions} granted")
            self.has_wallpaper_permission = True
        else:
            logger.debug(f"Permissions {permissions} denied")
            self.has_wallpaper_permission = False


DM = DeviceManager()


def start_profiler():
    import cProfile
    profile = cProfile.Profile()
    profile.enable()
    return profile


def stop_profiler(profile):
    profile.disable()
        
    profiler_dir = os.path.join(os.getcwd(), "profiler", "data")
    os.makedirs(profiler_dir, exist_ok=True)
    
    profile_path = os.path.join(profiler_dir, "myapp.profile")
    profile.dump_stats(profile_path)

    if DM.is_android:
        try:
            from android.storage import primary_external_storage_path  # type: ignore
            from jnius import autoclass  # type: ignore
            import shutil
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            ext_path = primary_external_storage_path()
            dest_dir = os.path.join(ext_path, "Documents", "BGTask")
            
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            dest_file = os.path.join(dest_dir, f"profile_{timestamp}.profile")
            shutil.copy2(profile_path, dest_file)
            
            MediaScannerConnection = autoclass("android.media.MediaScannerConnection")
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            MediaScannerConnection.scanFile(activity, [dest_file], None, None)

            print(f"Profile exported to: {dest_file}")
            
        except Exception as e:
            print(f"Error exporting profile: {str(e)}")