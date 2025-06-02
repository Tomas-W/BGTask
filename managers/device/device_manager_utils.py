import os

from typing import Final

from service import SERVICE_DIR
from src import SRC_DIR

class Dirs:
    """Contains directories for the App and Service."""
    def __init__(self, is_android: bool):
        # App source directory
        self.SRC: Final[str] = SRC_DIR
        # Service source directory
        self.SERVICE: Final[str] = self._get_storage_path(is_android, SERVICE_DIR)
        
        self.ASSETS: Final[str] = os.path.join(self.SRC, "assets")
        self.IMG: Final[str] = os.path.join(self.SRC, self.ASSETS, "images")

        # App sound
        self.ALARMS: Final[str] = self._get_storage_path(is_android, os.path.join(self.ASSETS, "alarms"))
        self.RECORDINGS: Final[str] = self._get_storage_path(is_android, os.path.join(self.ASSETS, "recordings"))
        # Service sound
        self.SERVICE_ALARMS_DIR: Final[str] = self._get_storage_path(is_android, "app/src/assets/alarms")
        self.SERVICE_RECORDINGS_DIR: Final[str] = self._get_storage_path(is_android, "app/src/assets/recordings")
    
    @staticmethod
    def _get_storage_path(is_android: bool, directory: str) -> str:
        """
        Returns storage path for the given directory.
        If Android, returns the path to the private directory.
        """
        if is_android:
            return os.path.join(os.environ["ANDROID_PRIVATE"], directory)
        else:
            return os.path.join(directory)

class Paths(Dirs):
    """Contains file paths for the App and Service."""
    def __init__(self, is_android: bool):
        super().__init__(is_android)
        # Navigation icons
        self.BACK_IMG: Final[str] = os.path.join(self.IMG, "back_64.png")
        self.EDIT_IMG: Final[str] = os.path.join(self.IMG, "edit_64.png")
        # self.HISTORY_IMG: Final[str] = os.path.join(self.IMG, "history_64.png")
        self.OPTIONS_IMG: Final[str] = os.path.join(self.IMG, "options_64.png")
        self.OPTIONS_IMG_BLACK: Final[str] = os.path.join(self.IMG, "options_black_64.png")
        self.SCREENSHOT_IMG: Final[str] = os.path.join(self.IMG, "screenshot_64.png")
        self.SETTINGS_IMG: Final[str] = os.path.join(self.IMG, "settings_64.png")
        self.EXIT_IMG: Final[str] = os.path.join(self.IMG, "exit_64.png")

        # Task icons
        self.SOUND_IMG: Final[str] = os.path.join(self.IMG, "sound_64.png")
        self.VIBRATE_IMG: Final[str] = os.path.join(self.IMG, "vibrate_64.png")
        
        # Playback icons
        self.PLAY_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "play_active_64.png")
        self.PLAY_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "play_inactive_64.png")
        self.STOP_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "stop_active_64.png")
        self.STOP_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "stop_inactive_64.png")
        self.EDIT_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "edit_active_64.png")
        self.EDIT_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "edit_inactive_64.png")
        self.DELETE_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "delete_active_64.png")
        self.DELETE_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "delete_inactive_64.png")
        
        # Task file
        self.TASK_FILE: Final[str] = os.path.join(self.ASSETS, "task_file.json")
        self.SERVICE_TASK_FILE: Final[str] = self._get_storage_path(is_android, "app/src/assets/task_file.json")

        # Flags
        self.SERVICE_HEARTBEAT_FLAG: Final[str] = self._get_storage_path(is_android, "app/service/service_heartbeat.flag")
                
        # Screenshot
        self.SCREENSHOT_PATH: Final[str] = os.path.join(self.IMG, "bgtask_screenshot.png")

class Dates:
    """Contains date format patterns for string formatting for the App and Service."""
    def __init__(self):
        # Main
        self.DATE_KEY: Final[str] = "%Y-%m-%d"              # 2024-03-21
        self.TIMESTAMP: Final[str] = "%Y-%m-%dT%H:%M:%S"    # 2024-03-21T14:30:00
        
        # Task
        self.TASK_HEADER: Final[str] = "%A %d %b"           # Thursday 21 Mar
        self.TASK_TIME: Final[str] = "%H:%M"                # 14:30
        
        # Calendar
        self.CALENDAR_DAY: Final[str] = "%A %d"             # Thursday 21
        self.MONTH_DAY: Final[str] = "%b %d"                # March 21
        self.DAY_MONTH_YEAR: Final[str] = "%d %b %Y"        # 21 Mar 2024
        self.DATE_SELECTION: Final[str] = "%A, %b %d, %Y"   # Thursday, March 21, 2024
        self.SELECTED_TIME: Final[str] = "%H:%M"            # 14:30
        
        # Components
        self.HOUR: Final[str] = "%H"                        # 14
        self.MINUTE: Final[str] = "%M"                      # 30
        
        # Recording
        self.RECORDING: Final[str] = "%H_%M_%S"             # 14_30_45

class Extensions:
    """Contains file extensions for the App and Service."""
    def __init__(self):
        # Audio formats
        self.WAV: Final[str] = ".wav"


class ServiceActions:
    """
    Contains action variables for the Service.
    Also used by App to communicate with Service.
    """
    def __init__(self):
        self.STOP_ALARM: Final[str] = "STOP_ALARM"
        self.SNOOZE_A: Final[str] = "SNOOZE_A"
        self.SNOOZE_B: Final[str] = "SNOOZE_B"
        self.CANCEL: Final[str] = "CANCEL"
        self.UPDATE_TASKS: Final[str] = "UPDATE_TASKS"
        self.REMOVE_TASK_NOTIFICATIONS: Final[str] = "REMOVE_TASK_NOTIFICATIONS"

        # Service only
        self.OPEN_APP: Final[str] = "OPEN_APP"
        self.RESTART_SERVICE: Final[str] = "RESTART_SERVICE"


class NotificationChannels:
    """
    Contains constants for notification channels.
    Used solely by Service.
    """
    def __init__(self):
        self.FOREGROUND: str = "foreground_channel"
        self.TASKS: str = "tasks_channel"

class NotificationPriority:
    """
    Contains constants for notification priorities.
    Used solely by Service.
    """
    def __init__(self):
        from jnius import autoclass  # type: ignore
        NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
        
        self.LOW: int = NotificationCompat.PRIORITY_LOW
        self.DEFAULT: int = NotificationCompat.PRIORITY_DEFAULT
        self.HIGH: int = NotificationCompat.PRIORITY_HIGH
        self.MAX: int = NotificationCompat.PRIORITY_MAX

class NotificationImportance:
    """
    Contains constants for notification channel importance.
    Used solely by Service.
    """
    def __init__(self):
        from jnius import autoclass  # type: ignore
        AndroidNotificationManager = autoclass("android.app.NotificationManager")
        
        self.LOW: int = AndroidNotificationManager.IMPORTANCE_LOW
        self.DEFAULT: int = AndroidNotificationManager.IMPORTANCE_DEFAULT
        self.HIGH: int = AndroidNotificationManager.IMPORTANCE_HIGH

class PendingIntents:
    """
    Contains constants for pending intents.
    Used solely by Service.
    """
    def __init__(self):
        self.OPEN_APP: int = 11
        self.SNOOZE_A: int = 12
        self.SNOOZE_B: int = 13
        self.CANCEL: int = 14


class NotificationType:
    """
    Contains constants for notification types.
    Used solely by Service.
    """
    def __init__(self):
        self.FOREGROUND: str = "foreground"
        self.EXPIRED: str = "expired"
