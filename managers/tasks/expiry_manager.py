import json

from datetime import datetime, timedelta
from typing import Any

from managers.tasks.task_manager_utils import Task
from managers.device.device_manager import DM

from src.utils.logger import logger


class ExpiryManager():
    """
    Base class for managing Tasks expiration.
    - Is extended upon my AppExpiryManager and ServiceExpiryManager.
    - Mainly handles expiry related logic.
    """	
    def __init__(self):
        super().__init__()
        self.task_file_path: str = DM.PATH.TASK_FILE
        if not DM.validate_file(self.task_file_path):
            logger.error(f"Task file not found: {self.task_file_path}")
            return
        
        self.expired_task: Task | None = None
        self.active_tasks: list[Task] = self._get_active_tasks()
        self.current_task: Task | None = self.get_current_task()

        self._need_refresh_tasks: bool = False

        self.SNOOZE_A_SECONDS: int = 60
        self._SNOOZE_B_SECONDS: int = 3600
    
    def _bind_audio_manager(self, audio_manager) -> None:
        """
        Binds the audio manager to the ExpiryManager.
        Cannot init immediately due to loading order.
        """
        self.audio_manager = audio_manager
    
    def _get_task_data(self) -> dict[str, list[dict[str, Any]]]:
        """Returns a dictionary of Tasks from the Task file."""
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

        # Load Task dictionary
        for tasks_data in task_data.values():
            tasks = [Task.to_class(task_dict) for task_dict in tasks_data]
            # Make Task objects and filter by expired
            non_expired_tasks = [
                task for task in tasks 
                if not task.expired and not (self.expired_task and task.task_id == self.expired_task.task_id)
            ]
            active_tasks.extend(non_expired_tasks)
        
        # Sort by effective time
        active_tasks.sort(key=self.get_effective_time)

        return active_tasks

    def refresh_active_tasks(self) -> None:
        """Re-loads active Tasks to get the latest data."""
        self.active_tasks = self._get_active_tasks()

    def refresh_current_task(self) -> None:
        """Re-loads the current Task to get the latest data."""
        self.current_task = self.get_current_task()
    
    def get_current_task(self) -> Task | None:
        """Returns the first Task that is not expired and is not the current expired Task."""
        try:
            if not self.active_tasks or len(self.active_tasks) == 0:
                return None
            
            return self.active_tasks[0]

        except Exception as e:
            logger.error(f"Error getting current Task: {e}")
            return None
    
    def is_task_expired(self) -> bool:
        """Returns True if the current Task is expired."""
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
        
        # Set as expired_task (not marked as expired - wait for user action)
        self.expired_task = self.current_task
        logger.debug(f"Set task {self.expired_task.task_id} as expired task")
        
        # Re-load Tasks
        self.refresh_active_tasks()
        self.refresh_current_task()

        return self.expired_task
    
    def _refresh_tasks(self) -> None:
        """Re-loads Tasks, re-load current and reset expired Task."""
        self.refresh_active_tasks()
        self.refresh_current_task()
        self.expired_task = None
    
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
    
    def clear_expired_task(self) -> None:
        """Clears the expired Task without saving changes."""
        if self.expired_task:
            logger.debug(f"Clearing expired Task {self.expired_task.task_id}")
            self.expired_task = None
    
    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a Task object by its ID."""
        if self.current_task and self.current_task.task_id == task_id:
            return self.current_task
        
        if self.expired_task and self.expired_task.task_id == task_id:
            return self.expired_task
        
        for task in self.active_tasks:
            if task.task_id == task_id:
                return task
        
        return None
    
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
                        import time
                        time.sleep(0.1)
                        logger.debug(f"Saved changes for Task {task_id}: {changes}")
                        return
        
        except Exception as e:
            logger.error(f"Error saving Task changes: {e}")
    
    @staticmethod
    def get_effective_time(task: Task) -> datetime:
        """Returns the Task's timestamp + snooze_time."""
        snooze_seconds = getattr(task, "snooze_time", 0)
        return task.timestamp + timedelta(seconds=snooze_seconds)
