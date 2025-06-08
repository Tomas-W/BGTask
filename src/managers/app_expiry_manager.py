from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

from managers.tasks.expiry_manager import ExpiryManager
from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from src.managers.app_task_manager import TaskManager
    from src.managers.app_communication_manager import AppCommunicationManager
    from managers.tasks.task import Task


class AppExpiryManager(ExpiryManager, EventDispatcher):
    def __init__(self):
        super().__init__()
        self.task_manager: "TaskManager" = None                       # connected in main.py
        self.communication_manager: "AppCommunicationManager" = None  # connected in main.py

        # Expiry events
        self.register_event_type("on_task_expired_show_task_popup")
        self.register_event_type("on_task_expired_trigger_alarm")
        self.register_event_type("on_task_expired_remove_task_notifications")

        # AlarmManager events
        self.register_event_type("on_task_cancelled_stop_alarm")
        self.register_event_type("on_task_snoozed_stop_alarm")

        self._just_resumed: bool = True
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

        if self.is_task_expired():
            logger.debug("Task expired, showing notification")

            # Only handle new task expiry if there isn't already an expired task
            if not self.expired_task:
                expired_task = self.handle_task_expired()
                if expired_task:
                    self.dispatch("on_task_expired_show_task_popup", task=expired_task)
                    self.dispatch("on_task_expired_remove_task_notifications")

                if expired_task and not self._just_resumed:
                    # self.dispatch("on_task_expired_trigger_alarm", task=expired_task)
                    pass
        
        self._just_resumed = False

    def _handle_cancelled_task(self, cancelled_task: "Task") -> None:
        """
        Cancels a Task by ID.
        - Stops the alarm.
        - Refreshes ExpiryManager.
        - Refreshes HomeScreen.
        - Refreshes StartScreen.
        - Refreshes ServiceExpiryManager.
        """
        logger.debug(f"Handling cancelled Task: {DM.get_task_log(cancelled_task)}")
        # Stop alarm
        self.dispatch("on_task_cancelled_stop_alarm")
        # Refresh ExpiryManager
        self._refresh_tasks()
        # Refresh HomeScreen
        self.task_manager._update_tasks_ui(task=cancelled_task, scroll_to_task=True)
        # Refresh StartScreen
        self.task_manager.dispatch("on_task_edit_refresh_start_screen")
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
        
    def _handle_snoozed_task(self, snoozed_task: "Task") -> None:
        """
        Snoozes a Task through a Popup.
        - Stops the alarm.
        - Refreshes ExpiryManager.
        - Refreshes HomeScreen.
        - Refreshes StartScreen.
        - Refreshes ServiceExpiryManager.
        """
        logger.debug(f"Handling snoozed Task: {DM.get_task_log(snoozed_task)}")
        # Stop alarm
        self.dispatch("on_task_snoozed_stop_alarm")
        # Refresh ExpiryManager
        self._refresh_tasks()
        # Refresh HomeScreen
        self.task_manager._update_tasks_ui(task=snoozed_task, scroll_to_task=True)
        # Refresh StartScreen
        self.task_manager.dispatch("on_task_edit_refresh_start_screen")
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
        
    def log_expiry_tasks(self) -> None:
        """Logs the expiry Tasks."""
        if self.log_tick % 10 == 0:
            self._log_expiry_tasks()
    
    def on_task_expired_trigger_alarm(self, *args, **kwargs):
        """Default handler for on_task_expired_trigger_alarm event."""
        pass
    
    def on_task_expired_show_task_popup(self, *args, **kwargs):
        """Default handler for on_task_expired_show_task_popup event."""
        pass

    def on_task_cancelled_stop_alarm(self, *args, **kwargs):
        """Default handler for on_task_cancelled_stop_alarm event."""
        pass

    def on_task_snoozed_stop_alarm(self, *args, **kwargs):
        """Default handler for on_task_snoozed_stop_alarm event."""
        pass

    def on_task_expired_remove_task_notifications(self, *args, **kwargs):
        """Default handler for on_task_expired_remove_task_notifications event."""
        pass
