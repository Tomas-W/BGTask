import os
import sys
import time

from datetime import timedelta
from typing import Final, TYPE_CHECKING

from managers.device.device_manager_utils import (
    Dirs, Paths, Dates, Extensions,
    NotificationChannels, NotificationPriority, NotificationImportance, PendingIntents,
    NotificationType, Actions, ActionTargets
)
from src.utils.logger import logger

if TYPE_CHECKING:
    from managers.tasks.task import Task


class DeviceManager:
    """
    Contains constants and basic functions for the App and Service.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "is_android"):  # Only initialize once
            self.is_android: bool = self._device_is_android()

            self.DIR: Final[Dirs] = Dirs(self.is_android)
            self.PATH: Final[Paths] = Paths(self.is_android)
            self.DATE: Final[Dates] = Dates()
            self.EXT: Final[Extensions] = Extensions()
    	
            # Communication
            self.ACTION: Final[Actions] = Actions()
            self.ACTION_TARGET: Final[ActionTargets] = ActionTargets()
            self.NOTIFICATION_TYPE: Final[NotificationType] = NotificationType()

            # Service communication & notifications
            if self.is_android:
                self.CHANNEL: Final[NotificationChannels] = NotificationChannels()
                self.PRIORITY: Final[NotificationPriority] = NotificationPriority()
                self.IMPORTANCE: Final[NotificationImportance] = NotificationImportance()
                self.INTENT: Final[PendingIntents] = PendingIntents()

    def _device_is_android(self) -> bool:
        """Returns whether the App is running on Android."""
        return sys.platform == "linux" and "ANDROID_DATA" in os.environ

    @staticmethod
    def get_task_log(task: "Task") -> str:
        """
        Returns a formatted string of the Task.
        - Format: id | timestamp + snooze_time
        """
        id = task.task_id[:8]
        task_time = task.timestamp + timedelta(seconds=task.snooze_time)
        message = task.message
        return f"{id} | {task_time} | {message[:8]}"
    
    def validate_dir(self, dir_path) -> bool:
        """Validate and create a directory if it doesn't exist."""
        if not os.path.isdir(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                return True
            
            except PermissionError:
                logger.error(f"PermissionError: Cannot create directory {dir_path}")
                return False
            except FileNotFoundError:
                logger.error(f"FileNotFoundError: {dir_path}")
                return False
            except OSError as e:
                logger.error(f"OSError: {e}")
                return False

    def validate_file(self, path: str, max_attempts: int = 3) -> bool:
        """
        Validates and creates a file if it doesn't exist.
        Adds a small delay for Windows.
        """
        for attempt in range(max_attempts):
            try:
                # Windows delay
                if not DM.is_android and attempt > 0:
                    time.sleep(0.1)
                
                # Verify contents
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        if f.read(1024):
                            return True
            
            except Exception as e:
                logger.warning(f"Error validating file: {path} (attempt {attempt+1}): {e}")
                return False
        
        logger.error(f"Error validating file: {path}")
        return False
    
    def get_storage_path(self, path: str) -> str:
        """Returns the app-specific storage path for the given directory."""
        if self.is_android:
            return os.path.join(os.environ["ANDROID_PRIVATE"], path)
        else:
            return os.path.join(path)
    
    def validate_action(self, action: str) -> bool:
        """Validate if the action is valid."""
        return hasattr(self.ACTION, action)


DM = DeviceManager()
