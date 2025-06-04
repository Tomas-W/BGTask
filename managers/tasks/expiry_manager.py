import json
import math

from datetime import datetime, timedelta
from typing import Any, TYPE_CHECKING

from managers.tasks.task import Task
from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from managers.audio.audio_manager import AudioManager


class ExpiryManager():

    START_TASK_MESSAGE: str = "No upcoming tasks!\nPress + to add a new one."
    SNOOZE_A_SECONDS: int = 60
    SNOOZE_B_SECONDS: int = 3600

    """
    Base class for managing Tasks expiration.
    - Is extended upon my AppExpiryManager and ServiceExpiryManager.
    - Mainly handles expiry related logic.
    """	
    def __init__(self):
        super().__init__()

        self.audio_manager: "AudioManager" | None = None

        self.task_file_path: str = DM.PATH.TASK_FILE
        if not DM.validate_file(self.task_file_path):
            logger.error(f"Error validating Task file: {self.task_file_path}")
            return
        
        self.expired_task: Task | None = None
        self.active_tasks: list[Task] = self._get_active_tasks()
        self.current_task: Task | None = self.get_current_task()

        self._need_refresh_tasks: bool = False

        self.SNOOZE_A_SECONDS: int = ExpiryManager.SNOOZE_A_SECONDS
        self._SNOOZE_B_SECONDS: int = ExpiryManager.SNOOZE_B_SECONDS
    
    def _has_time_overlap(self, timestamp: datetime) -> bool:
        """Checks if the timestamp would overlap with another Task."""
        for task in self.active_tasks:
            task_effective_time = task.timestamp + timedelta(seconds=task.snooze_time)
            if task_effective_time == timestamp:
                return True
        
        return False
    
    def snooze_task(self, action: str, task_id: str) -> int | bool:
        """Snoozes a Task by ID and action."""
        # Snoozed newly expired or foreground notification Task
        logger.critical(f"Snoozing task_id: {task_id}")
        snoozed_task = self.get_task_by_id(task_id)
        old_task = False
        if not snoozed_task:
            # Old expired Task, search in expired Tasks aswell
            snoozed_task = self._search_expired_task(task_id)
            old_task = True
        
        if not snoozed_task:
            logger.error(f"Task {task_id} not found for snoozing")
            return
        
        task_expiration = snoozed_task.timestamp + timedelta(seconds=snoozed_task.snooze_time)
        now = datetime.now()

        if now > task_expiration or old_task:
            # Snoozed through Task notification
            # Task is already expired > add time since expiration
            time_diff_seconds = math.floor((now - task_expiration).total_seconds() / 10) * 10  # Round down to nearest 10 seconds
        else:
            # Snoozed through foreground notification
            # Task is not expired > no need to add time
            time_diff_seconds = 0

        # Update snooze time
        if action.endswith(DM.ACTION.SNOOZE_A):
            snooze_seconds = self.SNOOZE_A_SECONDS
        elif action.endswith(DM.ACTION.SNOOZE_B):
            snooze_seconds = self._SNOOZE_B_SECONDS
        else:
            return False
        
        # Always add the time that has passed since original expiration
        added_snooze_time = snooze_seconds + time_diff_seconds
        
        # Calculate new timestamp
        new_timestamp = snoozed_task.timestamp + timedelta(seconds=snoozed_task.snooze_time + added_snooze_time)
        # Check for overlaps with other Tasks
        while self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {snoozed_task.task_id} would overlap with another task, adding 10 seconds")
            added_snooze_time += 10
            new_timestamp = snoozed_task.timestamp + timedelta(seconds=snoozed_task.snooze_time + added_snooze_time)
        
        # If snoozed, clear expired Task
        if snoozed_task == self.expired_task:
            self.expired_task = None
        
        # Save changes
        self._save_task_changes(snoozed_task.task_id, {
            "snooze_time": snoozed_task.snooze_time + added_snooze_time,
            "expired": False
        })

        logger.trace(f"Task {DM.get_task_log(snoozed_task)} snoozed for {added_snooze_time/60:.1f}m plus {time_diff_seconds/60}m waiting time.")
        logger.trace(f"Last added snooze time: {added_snooze_time}s")

        self._handle_snoozed_task(snoozed_task)
    
    def cancel_task(self, task_id: str) -> None:
        """Cancels a Task by ID."""
        cancelled_task = self.get_task_by_id(task_id)
        if not cancelled_task:
            # Cancelling old expired Task through notification
            # No need to handle
            return
        
        # Save changes to file
        self._save_task_changes(cancelled_task.task_id, {"expired": True})

        # Clear expired task if it was cancelled
        if cancelled_task == self.expired_task:
            self.expired_task = None
        
        logger.debug(f"Called cancel_task for: {DM.get_task_log(cancelled_task)}")
        self._handle_cancelled_task(cancelled_task)
    
    def _bind_audio_manager(self, audio_manager: "AudioManager") -> None:
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
        Refreshes active and current Tasks.
        Returns the expired Task (for notifications/alarms).
        """
        if not self.current_task:
            return None
        
        # Store current task as expired before refreshing
        self.expired_task = self.current_task
        logger.trace(f"Task {self.expired_task.task_id} expired")
        
        # Re-load Tasks but don't reset expired Task
        self.refresh_active_tasks()
        self.refresh_current_task()

        return self.expired_task
    
    def _refresh_tasks(self) -> None:
        """Re-loads Tasks, re-load current and reset expired Task."""
        self.expired_task = None
        self.refresh_active_tasks()
        self.refresh_current_task()
    
    def clear_expired_task(self) -> None:
        """Clears the expired Task without saving changes."""
        if self.expired_task:
            logger.trace(f"Clearing expired Task {self.expired_task.task_id}")
            self.expired_task = None
    
    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a Task object by its ID."""
        # First check expired task
        if self.expired_task and self.expired_task.task_id == task_id:
            return self.expired_task
        
        # Then check active tasks
        for task in self.active_tasks:
            if task.task_id == task_id:
                return task
        
        return None
    
    def _search_expired_task(self, task_id: str) -> "Task | None":
        """Searches for the expired task"""
        tasks_data = self._get_task_data()
        for task_data in tasks_data.values():
            for task in task_data:
                if task["task_id"] == task_id:
                    return task
        return None
    
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
    
    def log_expiry_tasks(self) -> None:
        logger.debug(f"Current task: {DM.get_task_log(self.current_task) if self.current_task else None}")
        logger.debug(f"Expired task: {DM.get_task_log(self.expired_task) if self.expired_task else None}")
        logger.debug("Active tasks:")
        for task in self.active_tasks:
            logger.debug(f"  {DM.get_task_log(task)}")
    
    @staticmethod
    def get_effective_time(task: Task) -> datetime:
        """Returns the Task's timestamp + snooze_time."""
        snooze_seconds = getattr(task, "snooze_time", 0)
        return task.timestamp + timedelta(seconds=snooze_seconds)
