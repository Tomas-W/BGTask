from datetime import timedelta
from typing import TYPE_CHECKING

from managers.tasks.expiry_manager import ExpiryManager

from src.managers.device.device_manager import DM
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
        - Expired Task or current Task if no expired Task exists.
        - Updates the snooze time.
        - Refreshes the Tasks and gets new current Task.
        """
        task_to_snooze = self.expired_task or self.current_task
        if not task_to_snooze:
            logger.error("No Task to snooze")
            return
            
        # Update snooze time
        if action.endswith(DM.ACTION.SNOOZE_A):
            snooze_seconds = self.SNOOZE_A_SECONDS
        elif action.endswith(DM.ACTION.SNOOZE_B):
            snooze_seconds = self._SNOOZE_B_SECONDS
        else:
            self.audio_manager.stop_alarm()
            logger.error(f"IN APP SNOOZE ACTION: {action}")
            return
        
        # Calculate new timestamp
        new_timestamp = task_to_snooze.timestamp + timedelta(seconds=task_to_snooze.snooze_time + snooze_seconds)
        
        # Check for overlaps with other Tasks
        if self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {task_to_snooze.task_id} would overlap with another task, adding 10 seconds")
            snooze_seconds += 10
        
        # If snoozed, clear expired Task
        if task_to_snooze == self.expired_task:
            self.expired_task = None
        
        # Save changes
        task_to_snooze.snooze_time += snooze_seconds
        task_to_snooze.expired = False
        self._save_task_changes(task_to_snooze.task_id, {
            "snooze_time": task_to_snooze.snooze_time,
            "expired": False
        })
        logger.debug(f"Task {task_to_snooze.task_id} snoozed for {snooze_seconds/60:.1f} minutes ({snooze_seconds}s). Total snooze: {task_to_snooze.snooze_time/60:.1f}m")

        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()
    
    def cancel_task(self, task_id: str | None = None) -> None:
        """
        Cancels the expired task if it exists, otherwise cancels current task.
        User can cancel current task with the foreground notification.
        """
        if task_id is not None:
            task_to_cancel = self.get_task_by_id(task_id)
        else:
            task_to_cancel = self.expired_task or self.current_task
        if not task_to_cancel:
            return
            
        # Mark as expired after user action
        task_to_cancel.expired = True
        logger.debug(f"Task {task_to_cancel.task_id} cancelled and marked as expired")
        
        # Save changes to file
        self._save_task_changes(task_to_cancel.task_id, {"expired": True})
        
        # Clear expired task if it was cancelled
        if task_to_cancel == self.expired_task:
            self.expired_task = None
        
        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()
