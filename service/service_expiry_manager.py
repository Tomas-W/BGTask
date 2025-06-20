from typing import TYPE_CHECKING

from managers.tasks.expiry_manager import ExpiryManager
from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from service.service_audio_manager import ServiceAudioManager
    from managers.tasks.task import Task


class ServiceExpiryManager(ExpiryManager):
    """Expiry Manager for the Service."""	
    def __init__(self, audio_manager: "ServiceAudioManager"):
        super().__init__()
        self.audio_manager: "ServiceAudioManager" = audio_manager
    
    def _handle_snoozed_task(self, snoozed_task: "Task") -> None:
        """
        Snoozes a Task from notification.
        - Gets expired Task or current Task (if no expired Task exists).
        - Updates the snooze time.
        - Refreshes the Tasks and gets new current Task.
        """
        logger.debug(f"Snoozed Task: {DM.get_task_log(snoozed_task)}")
        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()
    
    def _handle_cancelled_task(self, cancelled_task: "Task") -> None:
        """
        Cancels the expired task if it exists, otherwise cancels current task.
        User can cancel current task with the foreground notification.
        """
        logger.debug(f"Cancelled Task: {DM.get_task_log(cancelled_task)}")
        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()
