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


def get_storage_path(directory):
    """Returns the app-specific storage path for the given directory."""
    if device_is_android():
        return os.path.join(os.environ['ANDROID_PRIVATE'], directory)
    else:
        return os.path.join(directory)


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


def validate_file(file_path):
    """Validate and create a file if it doesn't exist."""
    if not os.path.isfile(file_path):
        try:
            with open(file_path, "w") as f:
                pass

        except PermissionError:
            logger.error(f"Permission denied: Cannot create file {file_path}. Check app permissions.")
        except FileNotFoundError:
            logger.error(f"Invalid path: {file_path} does not exist.")
        except OSError as e:
            logger.error(f"OS error while creating {file_path}: {e}")

