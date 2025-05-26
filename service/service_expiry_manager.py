from datetime import timedelta
from typing import TYPE_CHECKING

from managers.tasks.expiry_manager import ExpiryManager

from service.service_device_manager import DM
from src.utils.logger import logger

if TYPE_CHECKING:
    from service.service_audio_manager import ServiceAudioManager

class ServiceExpiryManager(ExpiryManager):
    """
    Expiry Manager for the Service.

    """	
    def __init__(self, audio_manager: "ServiceAudioManager"):
        super().__init__()
        self.audio_manager: "ServiceAudioManager" = audio_manager
    
    def snooze_task(self, action: str) -> None:
        """
        Snoozes a Task from notification.
        - Gets expired Task or current Task (if no expired Task exists).
        - Updates the snooze time.
        - Refreshes the Tasks and gets new current Task.
        """
        snoozed_task = self.expired_task or self.current_task
        if not snoozed_task:
            logger.error("No Task to snooze")
            self.audio_manager.stop_alarm()
            return
        
        logger.debug(f"Called snooze_task for: {DM.get_task_log(snoozed_task)}")

        # Update snooze time
        if action.endswith(DM.ACTION.SNOOZE_A):
            snooze_seconds = self.SNOOZE_A_SECONDS
        elif action.endswith(DM.ACTION.SNOOZE_B):
            snooze_seconds = self._SNOOZE_B_SECONDS
        else:
            self.audio_manager.stop_alarm()
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
        
        # Save changes
        snoozed_task.snooze_time += snooze_seconds
        snoozed_task.expired = False
        self._save_task_changes(snoozed_task.task_id, {
            "snooze_time": snoozed_task.snooze_time,
            "expired": False
        })

        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()

        logger.debug(f"Task {snoozed_task.task_id} snoozed for {snooze_seconds/60:.1f} minutes ({snooze_seconds}s). Total snooze: {snoozed_task.snooze_time/60:.1f}m")
    
    def cancel_task(self, task_id: str | None = None) -> None:
        """
        Cancels the expired task if it exists, otherwise cancels current task.
        User can cancel current task with the foreground notification.
        """
        if task_id is not None:
            cancelled_task = self.get_task_by_id(task_id)
        else:
            cancelled_task = self.expired_task or self.current_task
        if not cancelled_task:
            logger.error("No Task to cancel")
            self.audio_manager.stop_alarm()
            return
        
        logger.debug(f"Called cancel_task for: {DM.get_task_log(cancelled_task)}")
        # Mark as expired after user action
        cancelled_task.expired = True
        logger.debug(f"Task {cancelled_task.task_id} cancelled and marked as expired")
        
        # Save changes to file
        self._save_task_changes(cancelled_task.task_id, {"expired": True})
        
        # Clear expired task if it was cancelled
        if cancelled_task == self.expired_task:
            self.expired_task = None
        
        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()

        logger.debug(f"Task {cancelled_task.task_id} cancelled")
