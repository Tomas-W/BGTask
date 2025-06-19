import json
import math

from datetime import datetime, timedelta
from typing import Any

from managers.tasks.task import Task
from managers.device.device_manager import DM

from src.utils.logger import logger


class ExpiryManager():

    SNOOZE_A_SECONDS: int = 60
    SNOOZE_B_SECONDS: int = 3600

    """
    Base class for managing Tasks expiration.
    - Is extended upon my AppExpiryManager and ServiceExpiryManager.
    - Mainly handles expiry related logic.
    """	
    def __init__(self):
        super().__init__()
        self.task_file_path: str = DM.PATH.TASK_FILE
        if not DM.validate_file(self.task_file_path):
            logger.error(f"Error validating Task file: {self.task_file_path}")
            return
        
        self.expired_task: Task | None = None
        self.active_tasks: list[Task] = self._get_active_tasks()
        self.current_task: Task | None = self.get_current_task()

        self.SNOOZE_A_SECONDS: int = ExpiryManager.SNOOZE_A_SECONDS
        self._SNOOZE_B_SECONDS: int = ExpiryManager.SNOOZE_B_SECONDS
    
    def snooze_task(self, action: str, task_id: str) -> int | bool:
        """
        Snoozes a Task by ID and action.
        - Adds time since Task expired.
        - Adds action's snooze time.
        - Adds time to avoid overlapping with other Tasks.
        - Main Manager handles the snoozed Task.
        """
        logger.debug(f"Snoozing Task with ID: {DM.get_task_id_log(task_id)}")

        # Snoozed newly expired or foreground notification Task
        result = self._get_snoozed_task(task_id)
        if not result:
            # No snoozed Task found
            return False
        
        # Get time between expiry and snoozing
        snoozed_task, is_old_task = result
        time_since_expiry = self._get_time_since_expiry(snoozed_task, is_old_task)
        # Get action's snooze time
        snooze_seconds = self._get_snooze_seconds(action)
        # Add time to avoid overlapping with other Tasks
        overlap_time = self._get_overlap_time(snoozed_task, snooze_seconds, time_since_expiry)
        # Total
        total_snooze_time = snooze_seconds + \
                            time_since_expiry + \
                            overlap_time
        
        # Clear if snoozed expired Task
        if snoozed_task == self.expired_task:
            self.expired_task = None
        
        # Save changes
        self._save_task_changes(snoozed_task.task_id, {
            "snooze_time": snoozed_task.snooze_time + total_snooze_time,
            "expired": False
        })

        logger.info(f"Snoozed Task {DM.get_task_log(snoozed_task)} for {snooze_seconds/60:.1f}m plus {time_since_expiry/60:.1f}m waiting time.")
        logger.info(f"Total added snooze time: {total_snooze_time}s")

        self._handle_snoozed_task(snoozed_task)
    
    def _get_snoozed_task(self, task_id: str) -> tuple[Task, bool] | None:
        """Returns the snoozed task by ID."""
        snoozed_task = self.get_task_by_id(task_id)
        old_task = False
        if not snoozed_task:
            # Old expired Task, search in expired Tasks aswell
            snoozed_task = self._search_expired_task(task_id)
            old_task = True
        
        if not snoozed_task:
            logger.error(f"Error getting snoozed Task, Task {DM.get_task_id_log(task_id)} not found")
            return None
        
        return snoozed_task, old_task
    
    def _get_time_since_expiry(self, snoozed_task: Task, is_old_task: bool) -> int:
        """Returns the time since the snoozed Task expired."""
        task_expiration = snoozed_task.timestamp + timedelta(seconds=snoozed_task.snooze_time)
        now = datetime.now()

        if now > task_expiration or is_old_task:
            # Snoozed through Task notification
            # Task is already expired > add time since expiration
            time_since_expiry = math.floor((now - task_expiration).total_seconds() / 10) * 10  # Round down to nearest 10 seconds
        else:
            # Snoozed through foreground notification
            # Task is not expired > no need to add time
            time_since_expiry = 0

        return time_since_expiry
    
    def _get_snooze_seconds(self, action: str) -> int:
        """Returns the snooze seconds based on the action."""
        if action.endswith(DM.ACTION.SNOOZE_A):
            return self.SNOOZE_A_SECONDS
        elif action.endswith(DM.ACTION.SNOOZE_B):
            return self._SNOOZE_B_SECONDS
        else:
            return 0
    
    def _get_overlap_time(self, snoozed_task: Task, snooze_seconds: int, time_since_expiry: int) -> int:
        """Returns the extra overlap time needed to avoid overlapping with other Tasks."""
        task_snooze = snoozed_task.snooze_time + snooze_seconds + time_since_expiry
        new_timestamp = snoozed_task.timestamp + timedelta(seconds=task_snooze)
        
        overlap_time = 0
        while self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {snoozed_task.task_id} would overlap with another task, adding 10 seconds")
            overlap_time += 10
            new_timestamp = snoozed_task.timestamp + timedelta(seconds=task_snooze + overlap_time)
        
        return overlap_time

    def _has_time_overlap(self, timestamp: datetime) -> bool:
        """Returns True if the timestamp overlaps with another Task."""
        for task in self.active_tasks:
            task_effective_time = task.timestamp + timedelta(seconds=task.snooze_time)
            if task_effective_time == timestamp:
                return True
        
        return False

    def cancel_task(self, task_id: str) -> None:
        """Cancels a Task by ID."""
        logger.debug(f"Cancelling Task with ID: {DM.get_task_id_log(task_id)}")
        
        cancelled_task = self.get_task_by_id(task_id)
        if not cancelled_task:
            # Cancelling old expired Task through notification
            # No need to handle
            # Should not happen
            logger.critical(f"Tried to cancel old Task - should not happen - error removing Task notifications?")
            return
        
        # Save changes to file
        self._save_task_changes(cancelled_task.task_id, {"expired": True})

        # Clear expired task if it was cancelled
        if cancelled_task == self.expired_task:
            self.expired_task = None
        
        self._handle_cancelled_task(cancelled_task)
        logger.debug(f"Cancelled Task: {DM.get_task_log(cancelled_task)}")
    
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
        logger.debug(f"Task {DM.get_task_log(self.expired_task)} expired")
        
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
    
    def _search_expired_task(self, task_id: str) -> Task | None:
        """Searches for the expired task"""
        tasks_data = self._get_task_data()
        for task_data in tasks_data.values():
            for task in task_data:
                if task["task_id"] == task_id:
                    return Task.to_class(task)
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
                        logger.debug(f"Saved changes for Task {DM.get_task_id_log(task_id)}")
                        return
        
        except Exception as e:
            logger.error(f"Error saving Task changes: {e}")
    
    def _log_expiry_tasks(self) -> None:
        logger.debug(f"Current task: {DM.get_task_log(self.current_task) if self.current_task else None}")
        logger.debug(f"Expired task: {DM.get_task_log(self.expired_task) if self.expired_task else None}")
        logger.debug("Active tasks:")
        for task in self.active_tasks[:3]:
            logger.debug(f"  {DM.get_task_log(task)}")
    
    @staticmethod
    def get_effective_time(task: Task) -> datetime:
        """Returns the Task's timestamp + snooze_time."""
        snooze_seconds = getattr(task, "snooze_time", 0)
        return task.timestamp + timedelta(seconds=snooze_seconds)
