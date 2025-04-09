import os

from datetime import datetime, timedelta
from functools import lru_cache

from src.utils.logger import logger

from src.settings import PLATFORM


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


@lru_cache(maxsize=32)
def get_task_header_text(date_input) -> str:
    """
    Returns formatted date string with relative day names (Today, Tomorrow, etc.)
    
    Args:
        date_input: Can be either:
            - A datetime.date/datetime object
            - A string in format "Monday 24 Mar"
    
    Returns:
        Formatted string like "Today, January 1" or "Tomorrow, January 2"
    """
    today = datetime.now().date()
    
    # Convert input to date object
    if isinstance(date_input, datetime):
        date = date_input.date()
    elif hasattr(date_input, 'day') and hasattr(date_input, 'month') and hasattr(date_input, 'year'):
        # This is a date object (has day, month, year attributes)
        date = date_input
    elif isinstance(date_input, str) and len(date_input.split()) >= 3:
        # Parse string in format "Monday 24 Mar"
        date_parts = date_input.split()
        day = int(date_parts[1])
        month = date_parts[2]
        current_year = datetime.now().year
        date = datetime.strptime(f"{day} {month} {current_year}", "%d %b %Y").date()
    else:
        # If we can't parse it, just return the input
        return str(date_input)
    
    # Now format the date consistently
    month_day = date.strftime("%B %d")
    if date == today:
        return f"Today, {month_day}"
    elif date == today - timedelta(days=1):
        return f"Yesterday, {month_day}"
    elif date == today + timedelta(days=1):
        return f"Tomorrow, {month_day}"
    return date.strftime("%A, %B %d, %Y")
