import os
import time

from typing import Final

from src.managers.device.device_manager_utils import Dirs, Paths, Dates, Extensions, AlarmActions
from src.utils.logger import logger

ANDROID = "android"
WINDOWS = "Windows"


class DeviceManager:
    """
    Manages device-related operations.
    """
    def __init__(self):
        self.is_android: bool = self._device_is_android()
        self.is_windows: bool = not self.is_android
        
        # Initialize paths
        self.DIR: Final[Dirs] = Dirs(self.is_android)
        self.PATH: Final[Paths] = Paths(self.is_android)
        self.DATE: Final[Dates] = Dates()
        self.EXT: Final[Extensions] = Extensions()

        self.ACTION: Final[AlarmActions] = AlarmActions()

    def _device_is_android(self) -> bool:
        """Returns whether the app is running on Android."""
        from kivy.utils import platform
        return platform == ANDROID

    def write_flag_file(self, path: str) -> None:
        """Writes a flag file to the given path."""
        try:
            with open(path, "w") as f:
                f.write("1")
            logger.debug(f"Wrote flag file: {path.split('/')[-1]}")
        
        except Exception as e:
            logger.error(f"Error writing flag file {path.split('/')[-1]}: {e}")
    
    def check_flag_file(self, path: str) -> bool:
        """Checks if a flag file exists at the given path."""
        try:
            return os.path.exists(path)
        
        except Exception as e:
            logger.error(f"Error checking flag file {path.split('/')[-1]}: {e}")
            return False
    
    def remove_flag_file(self, path: str) -> None:
        """Removes a flag file at the given path."""
        try:
            os.remove(path)
            logger.debug(f"Removed flag file: {path.split('/')[-1]}")
        
        except Exception as e:
            logger.error(f"Error removing flag file {path.split('/')[-1]}: {e}")
    
    def write_settings_file(self, path: str, setting: str) -> None:
        """Writes a settings file to the given path."""
        try:
            with open(path, "w") as f:
                f.write(setting)
            logger.debug(f"Wrote settings file: {path.split('/')[-1]}")
        
        except Exception as e:
            logger.error(f"Error writing settings file {path.split('/')[-1]}: {e}")
    
    def read_settings_file(self, path: str) -> str:
        """Reads a settings file from the given path."""
        try:
            if not os.path.exists(path):
                return None
            
            with open(path, "r") as f:
                return f.read()
        
        except Exception as e:
            logger.error(f"Error reading settings file {path.split('/')[-1]}: {e}")
            return None
    
    def remove_settings_file(self, path: str) -> None:
        """Removes a settings file at the given path."""
        try:
            os.remove(path)
            logger.debug(f"Removed settings file: {path.split('/')[-1]}")
        
        except Exception as e:
            logger.error(f"Error removing settings file {path.split('/')[-1]}: {e}")
    
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

    def validate_file(self, path: str, max_attempts: int = 3) -> bool:
        """
        Validate and create a file if it doesn't exist.
        Adds a small delay for Windows.
        """
        for attempt in range(max_attempts):
            try:
                # Windows delay
                if DM.is_windows and attempt > 0:
                    time.sleep(0.1)
                
                # Verify contents
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        if f.read(1024):
                            return True
            
            except Exception as e:
                logger.warning(f"File verification attempt {attempt+1} failed: {e}")
                return False
        
        logger.error(f"Failed to verify audio file: {path}")
        return False
    
    def get_storage_path(self, path: str) -> str:
        """Returns the app-specific storage path for the given directory."""
        if self.is_android:
            return os.path.join(os.environ["ANDROID_PRIVATE"], path)
        else:
            return os.path.join(path)


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