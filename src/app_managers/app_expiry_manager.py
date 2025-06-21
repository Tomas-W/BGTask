from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

from managers.tasks.expiry_manager import ExpiryManager
from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.app_task_manager import TaskManager
    from src.app_managers.app_communication_manager import AppCommunicationManager
    from managers.tasks.task import Task


class AppExpiryManager(ExpiryManager, EventDispatcher):

    LOG_INTERVAL: int = 10

    def __init__(self, app: "TaskApp"):
        super().__init__()
        self.app: "TaskApp" = app
        self.task_manager: "TaskManager" = None                       # connected in main.py
        self.communication_manager: "AppCommunicationManager" = None  # connected in main.py

        self.log_tick: int = 0
    
    def check_task_expiry(self, *args, **kwargs) -> bool:
        """
        Runs on schedule.
        - Logs expiry Tasks
        - Checks if the current Task is expired
        - If expired, shows a Popup
        - If confirmed, tells CommunicationManager to remove Task notifications
        """
        self.log_tick += 1
        self.log_expiry_tasks()

        # Check all Managers are loaded
        if not self._is_ready_for_expiry():
            return
        
        # Current Task time > now
        if self.is_task_expired():

            # Only handle one expired Task at a time
            if not self.expired_task:
                expired_task = self.handle_task_expired()
                if expired_task:
                    from managers.popups.popup_manager import POPUP
                    POPUP.show_task_popup(task=expired_task)
                    self.communication_manager.send_action(DM.ACTION.REMOVE_TASK_NOTIFICATIONS)
    
    def _is_ready_for_expiry(self) -> bool:
        """Returns True if all required Managers are loaded."""
        required_managers = [
            DM.LOADED.TASK_MANAGER,
            DM.LOADED.AUDIO_MANAGER
        ]
        return all(manager for manager in required_managers)

    def _handle_cancelled_task(self, cancelled_task: "Task") -> None:
        """
        Gets the date key from the cancelled Task and updates Managers.
        """
        # Store the date key before refreshing
        date_key = cancelled_task.get_date_key()
        self._update_managers(date_key)

        # Scroll to Task
        self.app.get_screen(DM.SCREEN.HOME).scroll_to_task(cancelled_task)
    
    def _handle_snoozed_task(self, snoozed_task: "Task") -> None:
        """
        Gets the date key from the snoozed Task and updates Managers.
        """
        # Store the date key before refreshing
        date_key = snoozed_task.get_date_key()

        self._update_managers(date_key)
        # Scroll to Task
        self.app.get_screen(DM.SCREEN.HOME).scroll_to_task(snoozed_task)
    
    def _update_managers(self, date_key: str) -> None:
        """Updates the managers."""
        # Refresh ExpiryManager
        self._refresh_tasks()
        # Refresh TaskManager
        self.task_manager.refresh_task_groups()
        # Update HomeScreen
        self.task_manager.update_home_after_changes(date_key)
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
    
    def _connect_task_manager(self, task_manager: "TaskManager") -> None:
        """Connects the TaskManager to the ExpiryManager."""
        self.task_manager = task_manager
    
    def _connect_communication_manager(self, communication_manager: "AppCommunicationManager") -> None:
        """Connects the CommunicationManager to the ExpiryManager."""
        self.communication_manager = communication_manager
        
    def log_expiry_tasks(self) -> None:
        """Logs the expiry Tasks."""
        if self.log_tick % AppExpiryManager.LOG_INTERVAL == 0:
            self._log_expiry_tasks()
