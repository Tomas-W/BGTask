import os

from datetime import datetime, timedelta
from typing import Any

from kivy.utils import platform

from src.utils.logger import logger

class DateFormats:
    """Date and time format patterns used throughout the application."""
    TASK_TIME = "%H:%M"                # 14:30
    MONTH_DAY = "%b %d"                # March 21



DATE = DateFormats()


def get_service_timestamp(task: Any) -> str:
    """
    Returns the timestamp in the format of the ServiceNotification
    This includes the snooze time
    """
    try:
        timestamp = task.timestamp + timedelta(seconds=task.snooze_time)
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        if timestamp.date() == today:
            return f"Today @ {timestamp.strftime(DATE.TASK_TIME)}"
        
        elif timestamp.date() == tomorrow:
            return f"Tomorrow @ {timestamp.strftime(DATE.TASK_TIME)}"
        
        else:
            return f"{timestamp.strftime(DATE.MONTH_DAY)} @ {timestamp.strftime(DATE.TASK_TIME)}"
    
    except Exception as e:
        logger.error(f"Error getting service timestamp: {e}")
        return "00:00:00"


def get_storage_path(path: str) -> str:
    """Returns the storage path"""
    app_dir = os.environ.get("ANDROID_PRIVATE", "")
    return os.path.join(app_dir, path)


def validate_path(path: str) -> None:
    """Validate and create a file if it doesn't exist."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not os.path.exists(path):
            with open(path, "w") as f:
                pass

    except PermissionError:
        logger.error(f"Permission denied: Cannot create file {path}. Check app permissions.")
    except Exception as e:
        logger.error(f"Error while creating {path}: {e}")


class Paths:
    """Constants for paths"""
    TASK_FILE: str = get_storage_path("app/src/assets/task_file.json")

    TASKS_CHANGED_FLAG: str = get_storage_path("app/service/tasks_changed.flag")
    SERVICE_TASK_NOTIFICATION_REMOVAL_FLAG = "app/src/service/task_notification_removal.flag"
    SERVICE_HEARTBEAT_FLAG: str = get_storage_path("app/service/service_heartbeat.flag")

    ALARMS_DIR: str = get_storage_path("app/src/assets/alarms")
    RECORDINGS_DIR: str = get_storage_path("app/src/assets/recordings")


if platform == "android":
    class NotificationChannels:
        """Constants for notification channels"""
        FOREGROUND: str = "foreground_channel"
        TASKS: str = "tasks_channel"

    class NotificationPriority:
        """Constants for notification priorities"""
        from jnius import autoclass  # type: ignore
        NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
        
        LOW: int = NotificationCompat.PRIORITY_LOW
        DEFAULT: int = NotificationCompat.PRIORITY_DEFAULT
        HIGH: int = NotificationCompat.PRIORITY_HIGH
        MAX: int = NotificationCompat.PRIORITY_MAX

    class NotificationImportance:
        """Constants for notification channel importance"""
        from jnius import autoclass  # type: ignore
        AndroidNotificationManager = autoclass("android.app.NotificationManager")
        
        LOW: int = AndroidNotificationManager.IMPORTANCE_LOW
        DEFAULT: int = AndroidNotificationManager.IMPORTANCE_DEFAULT
        HIGH: int = AndroidNotificationManager.IMPORTANCE_HIGH

    class NotificationActions:
        """Constants for notification actions"""
        OPEN_APP: str = "open_app"
        SNOOZE_A: str = "snooze_a"
        SNOOZE_B: str = "snooze_b"
        CANCEL: str = "stop"

    class PendingIntents:
        """Constants for pending intents"""
        OPEN_APP: int = 11
        SNOOZE_A: int = 12
        SNOOZE_B: int = 13
        CANCEL: int = 14


PATH = Paths()
if platform == "android":
    CHANNEL = NotificationChannels()
    PRIORITY = NotificationPriority()
    IMPORTANCE = NotificationImportance()
    ACTION = NotificationActions()
    INTENT = PendingIntents()
