import json
import math
import time

from datetime import datetime, timedelta
from typing import Any

from managers.tasks.task import Task
from managers.device.device_manager import DM

from src.utils.logger import logger


class ExpiryManager():

    SNOOZE_A_SECONDS: int = 30
    SNOOZE_B_SECONDS: int = 3600 * 10
    SNOOZE_OVERLAP_TIME: int = 10

    """
    Base class for managing Tasks expiration.
    - Is extended upon my AppExpiryManager and ServiceExpiryManager.
    - Mainly handles expiry related logic.
    """	
    def __init__(self):
        super().__init__()
        self.task_file_path: str = DM.PATH.TASK_FILE
        if not self._validate_task_data():
            self._reset_task_file()
        
        self.expired_task: Task | None = None
        self.active_tasks: list[Task] = self._get_active_tasks()
        self.current_task: Task | None = self.get_current_task()
    
    def snooze_task(self, action: str, task_id: str) -> int | bool:
        """
        Snoozes a Task by ID and action.
        - Finds the Task.
        - Adds time since Task expired.
        - Adds action's snooze time.
        - Adds time to avoid overlapping with other Tasks.
        - ExpiryManager handles updating Managers.
        """
        # Check is expired Task or foreground notification Task
        # If expired Task -> is_old_task = True
        result = self._get_snoozed_task(task_id)
        if not result:
            return False
        
        snoozed_task, is_expired_task = result
        if snoozed_task == self.expired_task:
            self.expired_task = None
        
        total_snooze_time = self._get_snooze_time(snoozed_task, action, is_expired_task)
        snoozed_task.expired = False
        new_timestamp = snoozed_task.timestamp + timedelta(seconds=total_snooze_time)
        
        # If snoozed to new date, remove from old and add to new DateGroup
        # Otherwise just save changes
        if not self._has_changed_task_groups(snoozed_task, new_timestamp, total_snooze_time):
            self._save_task_changes(snoozed_task.task_id, {
                "timestamp": new_timestamp.isoformat(),
                "snooze_time": snoozed_task.snooze_time + total_snooze_time,
                "expired": False
            })
        
        logger.trace(f"Snoozed: {DM.get_task_log(snoozed_task)}")
        logger.trace(f"Added: {total_snooze_time/60:.1f}m for a total of {snoozed_task.snooze_time + total_snooze_time/60:.1f}m")

        self._handle_snoozed_task(snoozed_task)
    
    def cancel_task(self, task_id: str) -> None:
        """
        Cancels a Task by ID.
        - Finds the Task.
        - Sets a Task as expired.
        - Clears the expired Task.
        - ExpiryManager handles updating Managers.
        """
        logger.debug(f"Cancelling Task with ID: {DM.get_task_id_log(task_id)}")
        
        cancelled_task = self.get_active_task_by_id(task_id)
        if not cancelled_task:
            # Cancelling old expired Task through notification
            # No need to handle
            # Should not happen
            # Happened on Windows
            logger.critical(f"Tried to cancel old Task - should not happen: {task_id}")
            return
        
        # Save changes to file
        self._save_task_changes(cancelled_task.task_id, {"expired": True})

        # Clear expired task if it was cancelled
        if cancelled_task == self.expired_task:
            self.expired_task = None
        
        self._handle_cancelled_task(cancelled_task)
        logger.trace(f"Cancelled Task: {DM.get_task_log(cancelled_task)}")
    
    def _get_snooze_time(self, snoozed_task: Task, action: str, is_expired_task: bool) -> int:
        """
        Returns the total snooze time for a Task by:
        - Adding time since Task expired.
        - Adding action's snooze time.
        - Adding time to avoid overlapping with other Tasks.
        """
        # Get time between expiry and snoozing
        time_since_expiry = self._get_time_since_expiry(snoozed_task, is_expired_task)
        # Get action's snooze time
        snooze_seconds = self._get_snooze_seconds(action)
        # Add time to avoid overlapping with other Tasks
        overlap_time = self._get_overlap_time(snoozed_task, snooze_seconds, time_since_expiry)
        total_snooze_time = time_since_expiry + \
                            snooze_seconds + \
                            overlap_time
        
        return total_snooze_time
    
    def _get_snoozed_task(self, task_id: str) -> tuple[Task, bool] | None:
        """
        Returns the snoozed Task by ID and if it is an old expired Task.
        - Searches active Tasks first.
        - If not found, searches expired Tasks.
        """
        snoozed_task = self.get_active_task_by_id(task_id)
        old_task = False
        if not snoozed_task:
            # Old expired Task, search in expired Tasks aswell
            snoozed_task = self.get_any_task_by_id(task_id)
            old_task = True
        
        if not snoozed_task:
            logger.error(f"Error getting snoozed Task, Task {DM.get_task_id_log(task_id)} not found")
            return None
        
        return snoozed_task, old_task
    
    def _get_time_since_expiry(self, snoozed_task: Task, is_expired_task: bool) -> int:
        """Returns the time since the snoozed Task expired."""
        task_expiration = snoozed_task.timestamp
        now = datetime.now()

        if now > task_expiration or is_expired_task:
            # Snoozed through Task notification
            # Task is already expired -> add time since expiration
            time_since_expiry = math.floor((now - task_expiration).total_seconds() / 10) * 10  # Round down to nearest 10 seconds
        else:
            # Snoozed through foreground notification
            # Task is not expired -> no need to add time
            time_since_expiry = 0

        return time_since_expiry
    
    def _get_snooze_seconds(self, action: str) -> int:
        """Returns the snooze seconds based on the action."""
        if action.endswith(DM.ACTION.SNOOZE_A):
            return ExpiryManager.SNOOZE_A_SECONDS
        elif action.endswith(DM.ACTION.SNOOZE_B):
            return ExpiryManager.SNOOZE_B_SECONDS
    
    def _get_overlap_time(self, snoozed_task: Task, snooze_seconds: int, time_since_expiry: int) -> int:
        """Returns the extra overlap time needed to avoid overlapping with other Tasks."""
        new_snooze = snooze_seconds + time_since_expiry
        new_timestamp = snoozed_task.timestamp + timedelta(seconds=new_snooze)
        
        overlap_time = 0
        while self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {snoozed_task.task_id} would overlap with another task, adding {ExpiryManager.SNOOZE_OVERLAP_TIME} seconds")
            overlap_time += ExpiryManager.SNOOZE_OVERLAP_TIME
            new_timestamp = snoozed_task.timestamp + timedelta(seconds=new_snooze + overlap_time)
        
        return overlap_time

    def _has_time_overlap(self, timestamp: datetime) -> bool:
        """Returns True if the timestamp overlaps with another Task."""
        for task in self.active_tasks:
            if task.timestamp == timestamp:
                return True
        
        return False
    
    def get_task_data(self) -> dict[str, list[dict[str, Any]]]:
        """Returns a dictionary of Tasks from the Task file."""
        try:
            with open(self.task_file_path, "r") as f:
                data = json.load(f)
            return data
        
        except Exception as e:
            logger.error(f"Error getting Task data: {e}")
            return {}
    
    def _validate_task_data(self) -> bool:
        """
        Returns True if TaskData is valid, False otherwise.
        """
        data = self.get_task_data()

        if not isinstance(data, dict):
            return False
        
        for date_key, tasks_data in data.items():
            # Check date_key isstring
            if not isinstance(date_key, str):
                logger.error(f"Error validating TaskData, date_key != str: {type(date_key)=}")
                return False
            
            # Check tasks_data is list
            if not isinstance(tasks_data, list):
                logger.error(f"Error validating TaskData, tasks_data != list: {type(tasks_data)=}")
                return False
            
            # Check Tasks are dicts
            for task_data in tasks_data:
                if not isinstance(task_data, dict):
                    logger.error(f"Error validating TaskData, task_data != dict: {type(task_data)=}")
                    return False
        
        return True
    
    def _reset_task_file(self) -> None:
        """Saves empty JSON to file."""
        try:
            data = {}
            self.save_task_file(data)
        
        except Exception as e:
            logger.error(f"Error resetting Task file: {e}")
    
    def _get_active_tasks(self) -> list[Task]:
        """
        Returns a list of Tasks that are not marked as expired.
        Tasks are sorted by effective time (earliest first).
        """
        task_data = self.get_task_data()
        active_tasks = []

        # Load Tasks
        for tasks_data in task_data.values():
            tasks = [Task.to_class(task_dict) for task_dict in tasks_data]
            # Make Task objects and filter by expired
            non_expired_tasks = [
                task for task in tasks 
                if not task.expired and not (self.expired_task and task.task_id == self.expired_task.task_id)
            ]
            active_tasks.extend(non_expired_tasks)
        
        # Sort by timestamp
        active_tasks.sort(key=lambda task: task.timestamp)

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
            
            return datetime.now() >= self.current_task.timestamp
        
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
        
        # Store current Task as expired before refreshing
        self.expired_task = self.current_task
        # Re-load Tasks but don't reset expired Task
        self.refresh_active_tasks()
        self.refresh_current_task()
        logger.trace(f"Task expired, Tasks refreshed")

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
    
    def get_active_task_by_id(self, task_id: str) -> Task | None:
        """Get a Task object by its ID."""
        # First check expired Task
        if self.expired_task and self.expired_task.task_id == task_id:
            return self.expired_task
        
        # Then check active Tasks
        for task in self.active_tasks:
            if task.task_id == task_id:
                return task
        
        return None
    
    def get_any_task_by_id(self, task_id: str) -> Task | None:
        """Searches for the expired Task"""
        tasks_data = self.get_task_data()
        for task_data in tasks_data.values():
            for task in task_data:
                if task["task_id"] == task_id:
                    return Task.to_class(task)
        return None
    
    def _save_task_changes(self, task_id: str, changes: dict) -> None:
        """Saves Task changes to file."""
        try:
            task_data = self.get_task_data()
            for date_tasks in task_data.values():
                for task in date_tasks:
                    if task["task_id"] == task_id:
                        task.update(changes)
                        self.save_task_file(task_data)
                        
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
    
    def _add_to_task_groups(self, task: Task) -> None:
        """
        Adds a Task to the task_groups in the JSON file.
        """
        try:
            task_data = self.get_task_data()
            date_key = task.get_date_key()
            task.expired = False
            task_json = task.to_json()
            # Add to existing DateGroup or create new one
            if date_key in task_data:
                task_data[date_key].append(task_json)
            else:
                task_data[date_key] = [task_json]
            
            self.save_task_file(task_data)
            
            time.sleep(0.1)
            logger.debug(f"Added Task to group {date_key}: {DM.get_task_log(task)}")
            
        except Exception as e:
            logger.error(f"Error adding Task to groups: {e}")
    
    def save_task_file(self, data: dict) -> None:
        """Saves Task data to file."""
        try:
            with open(self.task_file_path, "w") as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving Task file: {e}")
    
    def _remove_from_task_groups(self, task: Task, date_key: str = None) -> None:
        """
        Removes a Task from the task_groups in the JSON file.
        If the last task is removed from a group, the entire group is removed.
        If no date_key is priveded, the Task's date_key is used.
        """
        try:
            task_data = self.get_task_data()
            date_key = date_key if date_key else task.get_date_key()
            
            if date_key not in task_data:
                logger.error(f"Date key {date_key} not found in task data")
                return
            
            # Find and remove the task
            tasks_in_date = task_data[date_key]
            for i, task_dict in enumerate(tasks_in_date):
                if task_dict["task_id"] == task.task_id:
                    tasks_in_date.pop(i)
                    
                    # If last Task in group, remove it
                    if not tasks_in_date:
                        del task_data[date_key]
                    
                    self.save_task_file(task_data)
                    
                    time.sleep(0.1)
                    logger.debug(f"Removed Task from group {date_key}: {DM.get_task_log(task)}")
                    return
            
            logger.error(f"Task {DM.get_task_log(task)} not found in group {date_key}")
            
        except Exception as e:
            logger.error(f"Error removing Task from groups: {e}")

    def _has_changed_task_groups(self, task: Task, new_timestamp: datetime, total_snooze_time: int) -> bool:
        """Handles moving a task to a different date group if needed. Returns True if moved, False otherwise."""
        old_date_key = task.get_date_key()
        task.timestamp = new_timestamp
        new_date_key = task.get_date_key()
        
        # Move if date changed
        # _add_to_task_groups un-expires Task
        if old_date_key != new_date_key:
            task.snooze_time += total_snooze_time
            self._remove_from_task_groups(task, old_date_key)
            self._add_to_task_groups(task)
            return True
        
        return False
