import os

from src.utils.logger import logger

from src.settings import PLATFORM, DIR


def device_is_android():
    """Returns whether the app is running on Android."""
    from kivy.utils import platform
    return platform == PLATFORM.ANDROID


def device_is_windows():
    """Returns whether the app is running on Windows."""
    import platform as py_platform
    return py_platform.system() == PLATFORM.WINDOWS


def get_storage_path(is_android, directory):
    """Returns the app-specific storage path for the given directory."""
    if is_android:
        try:
            from android.storage import app_storage_path  # type: ignore
            return os.path.join(app_storage_path(), directory)
        
        except ImportError:
            logger.error("Android storage module not available.")
            return os.path.join(os.path.expanduser("~"), directory)
    else:
        return os.path.join(directory)


def get_alarms_dir(is_android):
    """Get the directory path where the alarms are stored."""
    return get_storage_path(is_android, DIR.ALARMS)
    

def get_recordings_dir(is_android):
    """Get the directory path where the recordings are stored."""
    return get_storage_path(is_android, DIR.RECORDINGS)


def validate_dir(dir_path):
    """Validate and create a directory if it doesn't exist."""
    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

        except PermissionError:
            logger.error(f"Permission denied: Cannot create directory {dir_path}. Check app permissions.")
        except FileNotFoundError:
            logger.error(f"Invalid path: {dir_path} does not exist.")
        except OSError as e:
            logger.error(f"OS error while creating {dir_path}: {e}")
