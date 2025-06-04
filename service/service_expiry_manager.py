from datetime import timedelta, datetime
from typing import TYPE_CHECKING
import math

from managers.tasks.expiry_manager import ExpiryManager

from service.service_device_manager import DM
from src.utils.logger import logger

if TYPE_CHECKING:
    from service.service_audio_manager import ServiceAudioManager
    from managers.tasks.task import Task


class ServiceExpiryManager(ExpiryManager):
    """
    Expiry Manager for the Service.

    """	
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
        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()

        logger.trace(f"_handle_snoozed_task: {DM.get_task_log(snoozed_task)}")
    
    def _handle_cancelled_task(self, cancelled_task: "Task") -> None:
        """
        Cancels the expired task if it exists, otherwise cancels current task.
        User can cancel current task with the foreground notification.
        """
        # Stop alarm
        self.audio_manager.stop_alarm()
        # Refresh tasks
        self._refresh_tasks()

        logger.debug(f"_handle_cancelled_task: {DM.get_task_log(cancelled_task)}")
    
    

