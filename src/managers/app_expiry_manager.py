from datetime import timedelta

from kivy.event import EventDispatcher

from managers.tasks.expiry_manager import ExpiryManager
from src.managers.app_device_manager import DM

from src.utils.logger import logger


class AppExpiryManager(ExpiryManager, EventDispatcher):
    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager

        # Expiry events
        self.register_event_type("on_task_expired_show_task_popup")
        self.register_event_type("on_task_expired_trigger_alarm")

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
                
                if expired_task and not self._just_resumed:
                    self.dispatch("on_task_expired_trigger_alarm", task=expired_task)
        
        self._just_resumed = False

    def cancel_task(self, task_id: str) -> None:
        """
        Cancels a Task by ID.
        """
        cancelled_task = self.get_task_by_id(task_id)
        if not cancelled_task:
            self.dispatch("on_task_cancelled_stop_alarm")
            logger.error(f"Task with id {task_id} not found for cancellation")
            return
        
        logger.debug(f"Called cancel_task for: {DM.get_task_log(cancelled_task)}")

        # Save
        cancelled_task.expired = True
        self._save_task_changes(task_id, {
            "expired": cancelled_task.expired,
            "timestamp": cancelled_task.timestamp.isoformat(),
            "snooze_time": cancelled_task.snooze_time,
            })

        # Stop alarm
        self.dispatch("on_task_cancelled_stop_alarm")
        
        # Refresh tasks
        self._refresh_tasks()
        self.task_manager.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
        # Update UI
        self.task_manager._update_tasks_ui(task=cancelled_task, scroll_to_task=True)
        # Notify Service
        
        logger.debug(f"Task {cancelled_task.task_id} cancelled")
    
    def snooze_task(self, task_id: str, action: str) -> None:
        """
        Snoozes a Task by from Popup.
        - Gets expired Task or current Task (if no expired Task exists).
        - Updates the snooze time.
        - Refreshes the Tasks and gets new current Task.
        """
        logger.debug(f"Called snooze_task with task_id: {task_id} and action: {action}")
        snoozed_task = self.get_task_by_id(task_id)
        if not snoozed_task:
            self.dispatch("on_task_snoozed_stop_alarm")
            logger.error(f"Task with id {task_id} not found for snoozing")
            return
        
        # Update snooze time
        if action == DM.ACTION.SNOOZE_A:
            snooze_seconds = self.SNOOZE_A_SECONDS
        elif action == DM.ACTION.SNOOZE_B:
            snooze_seconds = self._SNOOZE_B_SECONDS
        else:
            self.dispatch("on_task_snoozed_stop_alarm")
            logger.error(f"Invalid snooze action: {action}")
            return
        
        # Calculate new timestamp
        new_timestamp = snoozed_task.timestamp + timedelta(seconds=snoozed_task.snooze_time + snooze_seconds)
        # Check for overlaps with other Tasks
        if self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {snoozed_task.task_id} would overlap with another task, adding 10 seconds")
            snooze_seconds += 10
        
        # If snoozed, clear expired Task
        if snoozed_task == self.expired_task:
            self.expired_task = None
        
        # Save
        snoozed_task.snooze_time += snooze_seconds
        snoozed_task.expired = False
        self._save_task_changes(task_id, {
            "expired": snoozed_task.expired,
            "timestamp": snoozed_task.timestamp.isoformat(),
            "snooze_time": snoozed_task.snooze_time,
            })

        # Stop alarm
        self.dispatch("on_task_snoozed_stop_alarm")
        # Refresh tasks
        self._refresh_tasks()
        self.task_manager.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
        # Update UI
        self.task_manager._update_tasks_ui(task=snoozed_task, scroll_to_task=True)
        # Notify Service

        logger.debug(f"Task {snoozed_task.task_id} snoozed for {snooze_seconds/60:.1f} minutes ({snooze_seconds}s). Total snooze: {snoozed_task.snooze_time/60:.1f}m")
    
    def check_expired_tasksbydate(self, instance, date: str):
        """Check if all Tasks are expired for a given date"""
        logger.debug(f"Checking expired tasks by date: {date}")
        from src.utils.misc import get_task_header_text
        formatted_date = get_task_header_text(date)
        
        for task_group in self.active_task_widgets:
            if task_group.date_str == formatted_date:
                if all(task.expired for task in task_group.tasks):
                    task_group.tasks_container.set_expired(True)
                    task_group.all_expired = True
                    logger.debug(f"All tasks expired for date: {formatted_date}")
                    return
        logger.debug(f"No expired tasks found for date: {formatted_date}")
    
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
