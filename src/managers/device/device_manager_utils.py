import os

from src import SRC_DIR
from typing import Final

class Dirs:
    """Class to hold directory paths with type hints"""
    def __init__(self, is_android: bool):
        # Use imported SRC_DIR
        self.SRC: Final[str] = SRC_DIR
        
        # Define base directories relative to src
        self.ASSETS: Final[str] = os.path.join(self.SRC, "assets")
        self.IMG: Final[str] = os.path.join(self.SRC, self.ASSETS, "images")
        
        # Define app directories
        self.ALARMS: Final[str] = self._get_storage_path(is_android, os.path.join(self.ASSETS, "alarms"))
        self.RECORDINGS: Final[str] = self._get_storage_path(is_android, os.path.join(self.ASSETS, "recordings"))
        print(f"ALARMS: {self.ALARMS}")
        print(f"RECORDINGS: {self.RECORDINGS}")
        
        # Define service directories (using app/ prefix)
        self.SERVICE_ALARMS_DIR: Final[str] = self._get_storage_path(is_android, "app/src/assets/alarms")
        self.SERVICE_RECORDINGS_DIR: Final[str] = self._get_storage_path(is_android, "app/src/assets/recordings")
        
        # Define root-level directories
        root_dir = os.path.dirname(self.SRC)  # One level up from src
        self.SERVICE: Final[str] = self._get_storage_path(is_android, os.path.join(root_dir, "service"))
        self.PROFILER: Final[str] = self._get_storage_path(is_android, os.path.join(root_dir, "profiler"))
    
    @staticmethod
    def _get_storage_path(is_android: bool, directory: str) -> str:
        """Returns the app-specific storage path for the given directory."""
        if is_android:
            return os.path.join(os.environ["ANDROID_PRIVATE"], directory)
        else:
            return os.path.join(directory)

class Paths(Dirs):
    """Class to hold file paths with type hints"""
    def __init__(self, is_android: bool):
        super().__init__(is_android)
        # Navigation images
        self.BACK_IMG: Final[str] = os.path.join(self.IMG, "back_64.png")
        self.EDIT_IMG: Final[str] = os.path.join(self.IMG, "edit_64.png")
        # self.HISTORY_IMG: Final[str] = os.path.join(self.IMG, "history_64.png")
        self.OPTIONS_IMG: Final[str] = os.path.join(self.IMG, "options_64.png")
        self.OPTIONS_IMG_BLACK: Final[str] = os.path.join(self.IMG, "options_black_64.png")
        self.SCREENSHOT_IMG: Final[str] = os.path.join(self.IMG, "screenshot_64.png")
        self.SETTINGS_IMG: Final[str] = os.path.join(self.IMG, "settings_64.png")
        self.EXIT_IMG: Final[str] = os.path.join(self.IMG, "exit_64.png")

        # Task images
        self.SOUND_IMG: Final[str] = os.path.join(self.IMG, "sound_64.png")
        self.VIBRATE_IMG: Final[str] = os.path.join(self.IMG, "vibrate_64.png")
        
        # Playback images
        self.PLAY_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "play_active_64.png")
        self.PLAY_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "play_inactive_64.png")
        self.STOP_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "stop_active_64.png")
        self.STOP_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "stop_inactive_64.png")
        self.EDIT_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "edit_active_64.png")
        self.EDIT_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "edit_inactive_64.png")
        self.DELETE_ACTIVE_IMG: Final[str] = os.path.join(self.IMG, "delete_active_64.png")
        self.DELETE_INACTIVE_IMG: Final[str] = os.path.join(self.IMG, "delete_inactive_64.png")
        
        # Task file paths
        self.TASK_FILE: Final[str] = os.path.join(self.ASSETS, "task_file.json")
        self.SERVICE_TASK_FILE: Final[str] = self._get_storage_path(is_android, "app/src/assets/task_file.json")

        # Flags
        self.TASKS_CHANGED_FLAG: Final[str] = os.path.join(self.SERVICE, "tasks_changed.flag")
        self.SERVICE_TASKS_CHANGED_FLAG: Final[str] = self._get_storage_path(is_android, "app/service/tasks_changed.flag")
        self.SERVICE_HEARTBEAT_FLAG: Final[str] = self._get_storage_path(is_android, "app/service/service_heartbeat.flag")

        # Screenshot
        self.SCREENSHOT_PATH: Final[str] = os.path.join(self.IMG, "bgtask_screenshot.png")
