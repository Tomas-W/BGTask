from datetime import timedelta

from managers.tasks.task_manager import TaskManager

from src.managers.tasks.task_manager_utils import Task
from service.service_utils import ACTION

from src.utils.logger import logger


class ServiceTaskManager(TaskManager):
    def __init__(self):
        super().__init__()
        self.task_file_path: str

        self.active_tasks: list[Task]
        self.expired_task: Task | None
        self.current_task: Task | None

        self._snooze_a_seconds: int
        self._snooze_b_seconds: int

    def snooze_task(self, action: str) -> None:
        """
        Snoozes the expired Task or current Task if no expired Task exists.
        """
        task_to_snooze = self.expired_task or self.current_task
        if not task_to_snooze:
            logger.error("No Task to snooze")
            return
            
        # Update snooze time
        if action.endswith(ACTION.SNOOZE_A):
            snooze_seconds = self._snooze_a_seconds
        elif action.endswith(ACTION.SNOOZE_B):
            snooze_seconds = self._snooze_b_seconds
        else:
            logger.error(f"Invalid snooze action: {action}")
            return
        
        # Calculate new timestamp
        new_timestamp = task_to_snooze.timestamp + timedelta(seconds=task_to_snooze.snooze_time + snooze_seconds)
        
        # Check for overlaps with other Tasks
        if self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {task_to_snooze.task_id} would overlap with another task, adding 10 seconds")
            snooze_seconds += 10
        
        # Save changes
        task_to_snooze.snooze_time += snooze_seconds
        self._save_task_changes(task_to_snooze.task_id, {
            "snooze_time": task_to_snooze.snooze_time
        })
        
        logger.debug(f"Task {task_to_snooze.task_id} snoozed for {snooze_seconds/60:.1f} minutes ({snooze_seconds}s). Total snooze: {task_to_snooze.snooze_time/60:.1f}m")
        
        # If snoozed, clear expired Task
        if task_to_snooze == self.expired_task:
            self.expired_task = None
        
        # Refresh Tasks from file and get new current Task
        # Snoozed Task becomes current if its new time is earlier
        self.active_tasks = self._get_active_tasks()
        self.current_task = self.get_current_task()
