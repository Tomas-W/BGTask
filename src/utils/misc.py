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


def is_widget_visible(widget, scroll_view):
    if not widget or not scroll_view:
        return False
    
    # Get ScrollView viewport size and position
    view_y = scroll_view.y
    view_height = scroll_view.height
    view_bottom = view_y
    view_top = view_y + view_height
    
    # Get widget position relative to ScrollView
    widget_y = widget.to_window(*widget.pos)[1] - scroll_view.to_window(0, 0)[1]
    widget_height = widget.height
    widget_bottom = widget_y
    widget_top = widget_y + widget_height
    
    # Check if widget is fully visible in viewport
    return widget_bottom >= view_bottom and widget_top <= view_top
