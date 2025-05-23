import json

from datetime import datetime, timedelta
from typing import Any

from src.managers.device.device_manager import DM
from src.managers.tasks.task_manager_utils import Task

from src.utils.logger import logger


class TaskManager:
    """
    Base class for managing Tasks.
    - Is extended upon my AppTaskManager and ServiceTaskManager.
    - Mainly handles expiry related logic.
    """	
    def __init__(self):
        self.task_file_path: str = DM.get_storage_path(DM.PATH.TASK_FILE)
        if not DM.validate_file(self.task_file_path):
            logger.error(f"Task file not found: {self.task_file_path}")
            return

        self.active_tasks: list[Task] = self._get_active_tasks()
        self.expired_task: Task | None = None
        self.current_task: Task | None = self.get_current_task()

        self._snooze_a_seconds: int = 60
        self._snooze_b_seconds: int = 3600

    def _get_task_data(self) -> dict[str, list[dict[str, Any]]]:
        """Returns a dictionary of Tasks from the task file."""
        try:
            with open(self.task_file_path, "r") as f:
                data = json.load(f)
            return data
        
        except Exception as e:
            logger.error(f"Error getting Task data: {e}")
            return {}
    
    def _get_active_tasks(self) -> list[Task]:
        """
        Returns a list of Tasks that are not marked as expired.
        Tasks are sorted by effective time (earliest first).
        """
        task_data = self._get_task_data()
        active_tasks = []

        # Convert all tasks to Task objects and filter by expired flag
        for tasks_data in task_data.values():
            tasks = [Task.to_class(task_dict) for task_dict in tasks_data]
            # Filter tasks that are not expired
            non_expired_tasks = [task for task in tasks if not task.expired]
            active_tasks.extend(non_expired_tasks)
        
        # Sort all tasks by effective time
        active_tasks.sort(key=self.get_effective_time)
        
        if not active_tasks:
            active_tasks = [self._get_start_task()]
        
        return active_tasks
    
    def get_current_task(self) -> Task | None:
        """Returns the first Task that isn't expired and isn't the current expired Task"""
        try:
            if not self.active_tasks:
                return None
                
            # Check all tasks to find the first one that isn't expired
            for task in self.active_tasks:
                # Skip if task is expired or is the current expired task
                if task.expired or (self.expired_task and task.task_id == self.expired_task.task_id):
                    continue
                return task

            return None

        except Exception as e:
            logger.error(f"Error getting current Task: {e}")
            return None
    
    def is_task_expired(self) -> bool:
        """Returns True if the current Task is expired"""
        try:
            if not self.current_task:
                return False
            
            task_time = self.current_task.timestamp
            trigger_time = task_time + timedelta(seconds=self.current_task.snooze_time)
            return datetime.now() >= trigger_time
        
        except Exception as e:
            logger.error(f"Error parsing timestamp: {e}")
            return False
    
    def handle_task_expired(self) -> Task | None:
        """
        Handles Task expiration by setting it as the expired Task and getting the next current Task.
        Returns the expired Task for notifications/alarms.
        """
        if not self.current_task:
            return None
        
        # Set as expired task (don't mark as expired - wait for user action)
        self.expired_task = self.current_task
        logger.debug(f"Set task {self.expired_task.task_id} as expired task")
        
        # Get next current task
        self.current_task = self.get_current_task()

        return self.expired_task
    
    def cancel_task(self) -> None:
        """
        Cancels the expired task if it exists, otherwise cancels current task.
        User can cancel current task with the foreground notification.
        """
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
        
        # Refresh Tasks and get new current Task
        self.active_tasks = self._get_active_tasks()
        self.current_task = self.get_current_task()

        logger.debug(f"Cancelled task")
    
    def snooze_task(self, action: str) -> None:
        """Implemented seperately."""
        pass
    
    def _has_time_overlap(self, timestamp: datetime) -> bool:
        """Checks if the snoozed Task or current Task would overlap with another Task."""
        for task in self.active_tasks:
            task_to_check = self.expired_task or self.current_task
            if task.task_id != task_to_check.task_id and not task.expired:
                    task_effective_time = task.timestamp + timedelta(seconds=task.snooze_time)
                    # Check within 1 second range
                    if abs((timestamp - task_effective_time).total_seconds()) < 1:
                        return True
        
        return False
    
    def refresh_current_task(self) -> None:
        """Refreshes the current Task."""
        self.current_task = self.get_current_task()
    
    def clear_expired_task(self) -> None:
        """Clears the expired Task without saving changes."""
        if self.expired_task:
            logger.debug(f"Clearing expired Task {self.expired_task.task_id}")
            self.expired_task = None
        
    def sort_active_tasks(self) -> None:
        """Sorts the active Task groups by the first Task's effective timestamp (timestamp + snooze_time)."""
        self.active_tasks.sort(key=lambda x: self.get_effective_time(x))
    
    def _get_start_task(self) -> Task:
        """Returns a start Task object."""
        return Task(timestamp=(datetime.now() - timedelta(minutes=1)).replace(second=0, microsecond=0),
                    message="No upcoming tasks!\nPress + to add a new one.",
                    expired=True)
    
    def _save_task_changes(self, task_id: str, changes: dict) -> None:
        """Saves Task changes to file"""
        try:
            task_data = self._get_task_data()
            for date_tasks in task_data.values():
                for task in date_tasks:
                    if task["task_id"] == task_id:
                        task.update(changes)
                        with open(self.task_file_path, "w") as f:
                            json.dump(task_data, f, indent=2)
                        
                        logger.debug(f"Saved changes for Task {task_id}: {changes}")
                        return
        
        except Exception as e:
            logger.error(f"Error saving Task changes: {e}")
    
    @staticmethod
    def get_effective_time(task: Task) -> datetime:
        """Returns the Task's timestamp + snooze_time."""
        snooze_seconds = getattr(task, "snooze_time", 0)
        return task.timestamp + timedelta(seconds=snooze_seconds)
