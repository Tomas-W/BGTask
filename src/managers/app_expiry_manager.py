from datetime import timedelta, datetime
from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

from managers.tasks.expiry_manager import ExpiryManager
from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from managers.tasks.task import Task


class AppExpiryManager(ExpiryManager, EventDispatcher):
    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager

        # Expiry events
        self.register_event_type("on_task_expired_show_task_popup")
        self.register_event_type("on_task_expired_trigger_alarm")
        self.register_event_type("on_task_expired_remove_task_notifications")

        # AlarmManager events
        self.register_event_type("on_task_cancelled_stop_alarm")
        self.register_event_type("on_task_snoozed_stop_alarm")

        self._just_resumed = False

        self.tick = 0
    
    def check_task_expiry(self, *args, **kwargs) -> bool:
        """Returns True if the current Task is expired"""
        self.tick += 1
        if self.tick % 10 == 0:
            logger.debug(f"Current task: {DM.get_task_log(self.current_task) if self.current_task else None}")
            logger.debug(f"Expired task: {DM.get_task_log(self.expired_task) if self.expired_task else None}")
            logger.debug("Active tasks:")

            for task in self.active_tasks:
                logger.debug(f"      {DM.get_task_log(task)}")
        
        if self._need_refresh_tasks:
            self._refresh_tasks()
            self._need_refresh_tasks = False

        if self.is_task_expired():
            logger.debug("Task expired, showing notification")

            # Only handle new task expiry if there isn't already an expired task
            if not self.expired_task:
                expired_task = self.handle_task_expired()
                if expired_task:
                    self.dispatch("on_task_expired_show_task_popup", task=expired_task)
                    self.dispatch("on_task_expired_remove_task_notifications")

                if expired_task and not self._just_resumed:
                    self.dispatch("on_task_expired_trigger_alarm", task=expired_task)
        
        self._just_resumed = False

    def _handle_cancelled_task(self, cancelled_task: "Task") -> None:
        """
        Cancels a Task by ID.
        """
        # Stop alarm
        self.dispatch("on_task_cancelled_stop_alarm")
        # Refresh ExpiryManager
        self._refresh_tasks()
        # Refresh HomeScreen
        self.task_manager._update_tasks_ui(task=cancelled_task, scroll_to_task=True)
        # Refresh StartScreen
        self.task_manager.dispatch("on_task_edit_refresh_start_screen")
        # Refresh ServiceExpiryManager
        self.task_manager.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
        
        logger.debug(f"_handle_cancelled_task: {DM.get_task_log(cancelled_task)}")
    
    def _handle_snoozed_task(self, snoozed_task: "Task") -> None:
        """
        Snoozes a Task by from Popup.
        - Gets expired Task or current Task (if no expired Task exists).
        - Updates the snooze time.
        - Refreshes the Tasks and gets new current Task.
        """
        # Stop alarm
        self.dispatch("on_task_snoozed_stop_alarm")
        # Refresh ExpiryManager
        self._refresh_tasks()
        # Refresh HomeScreen
        self.task_manager._update_tasks_ui(task=snoozed_task, scroll_to_task=True)
        # Refresh StartScreen
        self.task_manager.dispatch("on_task_edit_refresh_start_screen")
        # Refresh ServiceExpiryManager
        self.task_manager.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)

        logger.trace(f"_handle_snoozed_task updated Task: {DM.get_task_log(snoozed_task)}")

    # def check_expired_tasksbydate(self, instance, date: str):
    #     """Check if all Tasks are expired for a given date"""
    #     logger.debug(f"Checking expired tasks by date: {date}")
    #     from src.utils.misc import get_task_header_text
    #     formatted_date = get_task_header_text(date)
        
    #     for task_group in self.active_task_widgets:
    #         if task_group.date_str == formatted_date:
    #             if all(task.expired for task in task_group.tasks):
    #                 task_group.tasks_container.set_expired(True)
    #                 task_group.all_expired = True
    #                 logger.debug(f"All tasks expired for date: {formatted_date}")
    #                 return
    #     logger.debug(f"No expired tasks found for date: {formatted_date}")
    
    def on_task_expired_trigger_alarm(self, *args, **kwargs):
        """Default handler for on_task_expired_trigger_alarm event"""
        pass
    
    def on_task_expired_show_task_popup(self, *args, **kwargs):
        """Default handler for on_task_expired_show_task_popup event"""
        pass

    def on_task_cancelled_stop_alarm(self, *args, **kwargs):
        """Default handler for on_task_cancelled_stop_alarm event"""
        pass

    def on_task_snoozed_stop_alarm(self, *args, **kwargs):
        """Default handler for on_task_snoozed_stop_alarm event"""
        pass

    def on_task_expired_remove_task_notifications(self, *args, **kwargs):
        """Default handler for on_task_expired_remove_task_notifications event"""
        pass
