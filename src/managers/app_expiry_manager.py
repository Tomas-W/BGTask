from datetime import timedelta

from kivy.event import EventDispatcher

from managers.tasks.expiry_manager import ExpiryManager
from src.managers.device.device_manager import DM

from src.utils.logger import logger


class AppExpiryManager(ExpiryManager, EventDispatcher):
    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager
        self.register_event_type("on_task_expired_show_task_popup")
        self.register_event_type("on_task_expired_trigger_alarm")
        self.register_event_type("on_task_cancelled_stop_alarm")
        self.register_event_type("on_task_snoozed_stop_alarm")
        self.register_event_type("on_task_cancelled_update_ui")
        self.register_event_type("on_task_saved_scroll_to_task")
        self.tick = 0
    
    def check_task_expiry(self, *args, **kwargs) -> bool:
        """Returns True if the current Task is expired"""
        self.tick += 1
        if self.tick % 10 == 0:
            logger.debug(f"Current task: {self.current_task.task_id[:6] if self.current_task else None} | {self.current_task.timestamp + timedelta(seconds=self.current_task.snooze_time) if self.current_task else None}")
            logger.debug(f"Expired task: {self.expired_task.task_id[:6] if self.expired_task else None} | {self.expired_task.timestamp + timedelta(seconds=self.expired_task.snooze_time) if self.expired_task else None}")
            logger.debug("Active tasks:")

            for task in self.active_tasks:
                logger.debug(f"      {task.task_id[:6]} | {task.timestamp + timedelta(seconds=task.snooze_time)}")
        
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
                    self.dispatch("on_task_expired_trigger_alarm", task=expired_task)

    def cancel_task(self, task_id: str) -> None:
        """
        Cancels a Task by ID.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            self.dispatch("on_task_cancelled_stop_alarm")
            logger.error(f"Task with id {task_id} not found for cancellation")
            return
        
        # Save
        task.expired = True
        self._save_task_changes(task_id, {"expired": True})
        # Stop alarm
        self.dispatch("on_task_cancelled_stop_alarm")
        # Refresh tasks
        self._refresh_tasks()
        # Update UI
        self.dispatch("on_task_cancelled_update_ui")
        # Scroll to task
        self.dispatch("on_task_saved_scroll_to_task", task=task)
        # Notify Service
        DM.write_flag_file(DM.PATH.TASKS_CHANGED_FLAG)
    
    def snooze_task(self, task_id: str, action: str) -> None:
        """
        Snoozes a Task by ID.
        """
        logger.debug(f"called snooze_task with task_id: {task_id}")
        task = self.get_task_by_id(task_id)

        if not task:
            self.dispatch("on_task_snoozed_stop_alarm")
            logger.error(f"Task with id {task_id} not found for snoozing")
            return
        
        if action == DM.ACTION.SNOOZE_A:
            snooze_time = self.SNOOZE_A_SECONDS
        elif action == DM.ACTION.SNOOZE_B:
            snooze_time = self._SNOOZE_B_SECONDS
        else:
            self.dispatch("on_task_snoozed_stop_alarm")
            logger.error(f"Invalid snooze action: {action}")
            return
        
        # Save
        task.snooze_time += snooze_time
        self._save_task_changes(task_id, {"snooze_time": task.snooze_time})
        # Update UI
        self.task_manager._update_tasks_ui(task=task)
        # Refresh tasks
        self._refresh_tasks()
        # Notify Service
        DM.write_flag_file(DM.PATH.TASKS_CHANGED_FLAG)
        # Stop alarm
        self.dispatch("on_task_snoozed_stop_alarm")
    
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

    def on_task_cancelled_update_ui(self, *args, **kwargs):
        """Default handler for on_task_cancelled_update_ui event"""
        pass

    def on_task_saved_scroll_to_task(self, *args, **kwargs):
        """Default handler for on_task_saved_scroll_to_task event"""
        pass
