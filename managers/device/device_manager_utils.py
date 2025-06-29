import os

from typing import Final

from service import SERVICE_DIR
from src import SRC_DIR


class Dirs:
    """Contains directories for the App and Service."""
    def __init__(self, is_android: bool):
        # App
        self.SRC: Final[str] = SRC_DIR
        self.ASSETS: Final[str] = os.path.join(self.SRC, "assets")
        self.IMG: Final[str] = os.path.join(self.SRC, self.ASSETS, "images")
        self.ALARMS: Final[str] = self._get_storage_path(is_android, os.path.join(self.ASSETS, "alarms"))
        self.RECORDINGS: Final[str] = self._get_storage_path(is_android, os.path.join(self.ASSETS, "recordings"))
        # Service
        self.SERVICE: Final[str] = self._get_storage_path(is_android, SERVICE_DIR)
        self.SERVICE_ALARMS: Final[str] = self._get_storage_path(is_android, "app/src/assets/alarms")
        self.SERVICE_RECORDINGS: Final[str] = self._get_storage_path(is_android, "app/src/assets/recordings")
    
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
        # App
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
        self.SNOOZE_IMG: Final[str] = os.path.join(self.IMG, "snooze_64.png")
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
        self.TEST_FILE: Final[str] = os.path.join(self.ASSETS, "test_file.json")
        # Screenshot
        self.SCREENSHOT_PATH: Final[str] = os.path.join(self.IMG, "bgtask_screenshot.png")
        # Service
        self.SERVICE_TASK_FILE: Final[str] = self._get_storage_path(is_android, "app/src/assets/task_file.json")
        # Both
        self.SERVICE_HEARTBEAT_FLAG: Final[str] = self._get_storage_path(is_android, "app/service/service_heartbeat.flag")
        


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
        # Audio
        self.WAV: Final[str] = ".wav"


class Actions:
    """
    Contains action variables for sending actions between App and Service.
    """
    def __init__(self):
        # Service
        self.REMOVE_TASK_NOTIFICATIONS: Final[str] = "REMOVE_TASK_NOTIFICATIONS"
        self.RESTART_SERVICE: Final[str] = "RESTART_SERVICE"
        self.BOOT_ACTION: Final[str] = "android.intent.action"
        self.BOOT_COMPLETED: Final[str] = "BOOT_COMPLETED"
        # Both
        self.SNOOZE_A: Final[str] = "SNOOZE_A"
        self.SNOOZE_B: Final[str] = "SNOOZE_B"
        self.CANCEL: Final[str] = "CANCEL"
        self.STOP_ALARM: Final[str] = "STOP_ALARM"
        self.UPDATE_TASKS: Final[str] = "UPDATE_TASKS"


class ActionTargets:
    """
    Contains target variables for sending actions to either App or Service receiver (or both).
    - App's receiver listens to ACTION_TARGET: APP
    - Service's receiver listens to ACTION_TARGET: SERVICE | APP
    """
    def __init__(self):
        self.TARGET: Final[str] = "TARGET"
        self.SERVICE: Final[str] = "SERVICE"
        self.APP: Final[str] = "APP"


class NotificationChannels:
    """
    Contains constants for notification channels for the Service.
    """
    def __init__(self):
        self.FOREGROUND: str = "foreground_channel"
        self.TASKS: str = "tasks_channel"


class NotificationPriority:
    """
    Contains constants for notification priorities for the Service.
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
    Contains constants for notification channel importance for the Service.
    """
    def __init__(self):
        from jnius import autoclass  # type: ignore
        AndroidNotificationManager = autoclass("android.app.NotificationManager")
        
        self.LOW: int = AndroidNotificationManager.IMPORTANCE_LOW
        self.DEFAULT: int = AndroidNotificationManager.IMPORTANCE_DEFAULT
        self.HIGH: int = AndroidNotificationManager.IMPORTANCE_HIGH


class PendingIntents:
    """
    Contains constants for pending intents for the Service.
    """
    def __init__(self):
        self.SNOOZE_A: int = 11
        self.SNOOZE_B: int = 12
        self.CANCEL: int = 13
        self.OPEN_APP: int = 14
        self.STOP_ALARM: int = 15


class NotificationType:
    """
    Contains constants for notification types for the Service.
    """
    def __init__(self):
        self.FOREGROUND: str = "foreground"
        self.EXPIRED: str = "expired"


class Settings:
    """
    Contains constants for settings for the App and Service.
    """
    def __init__(self):
        # App
        self.ALARM_NAME_MIN_LENGTH: int = 4
        self.ALARM_NAME_MAX_LENGTH: int = 20
        # Both
        self.HEARTBEAT_SEDCONDS: int = 120


class Screens:
    """
    Contains constants for screens for the App.
    """
    def __init__(self):
        self.HOME = "HOME"
        self.WALLPAPER = "WALLPAPER"
        self.NEW_TASK = "NEW_TASK"
        self.SELECT_DATE = "SELECT_DATE"
        self.SELECT_ALARM = "SELECT_ALARM"
        self.SAVED_ALARMS = "SAVED_ALARMS"
        self.SETTINGS = "SETTINGS"
        self.MAP = "MAP_SCREEN"


class Trigger:
    """
    Contains constants for trigger sound and vibration for the App.
    """
    def __init__(self):
        self.OFF = "off"
        self.ONCE = "once"
        self.CONTINUOUSLY = "continuously"


class Loaded:
    """
    Contains constants that show whether App components are loaded or not.
    """
    def __init__(self):
        self.HOME_SCREEN = False
        self.WALLPAPER_SCREEN = False
        self.NEW_TASK_SCREEN = False
        self.SELECT_DATE_SCREEN = False
        self.SELECT_ALARM_SCREEN = False
        self.SAVED_ALARMS_SCREEN = False
        self.SETTINGS_SCREEN = False
        self.MAP_SCREEN = False

        self.SCREEN_MANAGER = False
        self.NAVIGATION_MANAGER = False
        self.EXPIRY_MANAGER = False
        self.TASK_MANAGER = False
        self.AUDIO_MANAGER = False
        self.COMMUNICATION_MANAGER = False
        self.PREFERENCE_MANAGER = False
        self.POPUP_MANAGER = False

        self.TASK_POPUP = False
        self.CONFIRMATION_POPUP = False
        self.CUSTOM_POPUP = False
        self.INPUT_POPUP = False
        self.SELECTION_POPUP = False


class Initialized:
    """
    Contains constants that show whether the Screen's UI is initialized.
    """
    def __init__(self):
        self.HOME_SCREEN = False
        self.WALLPAPER_SCREEN = False
        self.NEW_TASK_SCREEN = False
        self.SELECT_DATE_SCREEN = False
        self.SELECT_ALARM_SCREEN = False
        self.SAVED_ALARMS_SCREEN = False
        self.SETTINGS_SCREEN = False
        self.MAP_SCREEN = False
