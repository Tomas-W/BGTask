import os

from datetime import datetime, timedelta

from jnius import autoclass  # type: ignore

NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
AndroidNotificationManager = autoclass("android.app.NotificationManager")


class DateFormats:
    """Date and time format patterns used throughout the application."""
    DATE_KEY = "%Y-%m-%d"              # 2024-03-21
    TIMESTAMP = "%Y-%m-%dT%H:%M:%S"    # 2024-03-21T14:30:00

    TASK_HEADER = "%A %d %b"           # Thursday 21 Mar
    TASK_TIME = "%H:%M"                # 14:30

    SELECTED_TIME = "%H:%M"            # 14:30
    CALENDAR_DAY = "%A %d"             # Thursday 21
    HOUR = "%H"                        # 14
    MINUTE = "%M"                      # 30

    MONTH_DAY = "%b %d"                # March 21
    DAY_MONTH_YEAR = "%d %b %Y"        # 21 Mar 2024

    DATE_SELECTION = "%A, %b %d, %Y"   # Thursday, March 21, 2024

    RECORDING = "%H_%M_%S"             # 14_30_45


DATE = DateFormats()


def get_service_timestamp(task) -> str:
    """
    Returns the timestamp in the format of the ServiceNotification
    This includes the snooze time
    """
    timestamp = task.timestamp + timedelta(seconds=task.snooze_time)
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    if timestamp.date() == today:
        return f"Today @ {timestamp.strftime(DATE.TASK_TIME)}"
    elif timestamp.date() == tomorrow:
        return f"Tomorrow @ {timestamp.strftime(DATE.TASK_TIME)}"
    else:
        return f"{timestamp.strftime(DATE.MONTH_DAY)} @ {timestamp.strftime(DATE.TASK_TIME)}"


def get_storage_path(path):
        """Returns the storage path"""
        app_dir = os.environ.get("ANDROID_PRIVATE", "")
        return os.path.join(app_dir, path)


class Paths:
    """Constants for paths"""
    TASK_FILE = get_storage_path("app/src/assets/task_file.json")

    SERVICE_FLAG = get_storage_path("app/service/service_stop.flag")
    SNOOZE_A_FLAG = get_storage_path("app/service/snooze_a.flag")
    SNOOZE_B_FLAG = get_storage_path("app/service/snooze_b.flag")
    STOP_FLAG = get_storage_path("app/service/stop.flag")

    AUDIO_TASK_EXPIRED = get_storage_path("app/src/assets/alarms/rooster.wav")


class NotificationChannels:
    """Constants for notification channels"""
    FOREGROUND = "foreground_channel"
    TASKS = "tasks_channel"

class NotificationPriority:
    """Constants for notification priorities"""
    LOW = NotificationCompat.PRIORITY_LOW
    DEFAULT = NotificationCompat.PRIORITY_DEFAULT
    HIGH = NotificationCompat.PRIORITY_HIGH

class NotificationImportance:
    """Constants for notification channel importance"""
    LOW = AndroidNotificationManager.IMPORTANCE_LOW
    DEFAULT = AndroidNotificationManager.IMPORTANCE_DEFAULT
    HIGH = AndroidNotificationManager.IMPORTANCE_HIGH

class NotificationActions:
    """Constants for notification actions"""
    OPEN_APP = "open_app"
    SNOOZE_A = "snooze_a"
    SNOOZE_B = "snooze_b"
    CANCEL = "stop"

class PendingIntents:
    """Constants for pending intents"""
    OPEN_APP = 11
    SNOOZE_A = 12
    SNOOZE_B = 13
    CANCEL = 14


PATH = Paths()
CHANNEL = NotificationChannels()
PRIORITY = NotificationPriority()
IMPORTANCE = NotificationImportance()
ACTION = NotificationActions()
INTENT = PendingIntents()
