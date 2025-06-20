from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

from managers.tasks.expiry_manager import ExpiryManager
from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.app_task_manager import TaskManager
    from src.app_managers.app_audio_manager import AppAudioManager
    from src.app_managers.app_communication_manager import AppCommunicationManager
    from managers.tasks.task import Task


class AppExpiryManager(ExpiryManager, EventDispatcher):
    def __init__(self, app: "TaskApp"):
        super().__init__()
        self.app: "TaskApp" = app
        self.task_manager: "TaskManager" = None                       # connected in main.py
        self.audio_manager: "AppAudioManager" = None                  # connected in main.py
        self.communication_manager: "AppCommunicationManager" = None  # connected in main.py

        self.log_tick: int = 0
    
    def _connect_task_manager(self, task_manager: "TaskManager") -> None:
        """Connects the TaskManager to the ExpiryManager."""
        self.task_manager = task_manager
    
    def _connect_communication_manager(self, communication_manager: "AppCommunicationManager") -> None:
        """Connects the CommunicationManager to the ExpiryManager."""
        self.communication_manager = communication_manager
    
    def check_task_expiry(self, *args, **kwargs) -> bool:
        """Returns True if the current Task is expired."""
        self.log_tick += 1
        self.log_expiry_tasks()

        if self.is_task_expired() and self._is_ready_for_expiry() and self.app.tasks_are_reloaded:
            logger.debug("Task expired, showing notification")

            # Allows expired Tasks to 'stack' so they can be handled individually
            if not self.expired_task:
                expired_task = self.handle_task_expired()
                if expired_task:
                    from managers.popups.popup_manager import POPUP
                    POPUP._handle_task_popup(task=expired_task)
                    self.communication_manager.send_action(DM.ACTION.REMOVE_TASK_NOTIFICATIONS)
    
    def _is_ready_for_expiry(self) -> bool:
        """Returns True if the ExpiryManager is ready to check for Task expiry."""
        required_managers = [
            DM.LOADED.TASK_MANAGER,
            DM.LOADED.AUDIO_MANAGER
        ]
        return not any(not manager for manager in required_managers)

    def _handle_cancelled_task(self, cancelled_task: "Task") -> None:
        """
        Cancels a Task by ID.
        - Stops the alarm.
        - Refreshes ExpiryManager.
        - Refreshes HomeScreen.
        - Refreshes StartScreen.
        - Refreshes ServiceExpiryManager.
        """
        # Store the date key before refreshing
        date_key = cancelled_task.get_date_key()
        
        # Refresh ExpiryManager
        self._refresh_tasks()
        # Refresh TaskManager
        self.task_manager.refresh_task_groups()
        # Update HomeScreen
        self.task_manager.update_home_after_changes(date_key)
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
    
    def _stop_alarm(self) -> None:
        """Stops the alarm."""
        if not DM.LOADED.AUDIO_MANAGER:
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._stop_alarm(), 0.1)
            return
        
        logger.info("STOPPING ALARM")
        self.audio_manager.stop_alarm()

    def _handle_snoozed_task(self, snoozed_task: "Task") -> None:
        """
        Snoozes a Task through a Popup.
        - Refreshes ExpiryManager.
        - Refreshes TaskManager.
        - Refreshes HomeScreen.
        - Refreshes ServiceExpiryManager.
        """
        # Store the date key before refreshing
        date_key = snoozed_task.get_date_key()
        
        # Refresh ExpiryManager
        self._refresh_tasks()
        # Refresh TaskManager
        self.task_manager.refresh_task_groups()
        # Update HomeScreen
        self.task_manager.update_home_after_changes(date_key)
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
        
    def log_expiry_tasks(self) -> None:
        """Logs the expiry Tasks."""
        if self.log_tick % 10 == 0:
            self._log_expiry_tasks()
