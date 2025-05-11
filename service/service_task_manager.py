import json

from datetime import datetime, timedelta
from typing import Any

from src.managers.tasks.task_manager_utils import Task

from service.service_logger import logger
from service.service_utils import PATH, ACTION


class ServiceTaskManager:
    def __init__(self):
        self.task_file: str = PATH.TASK_FILE
        self.expired_task: Task | None = None  # Initialize expired_task first
        self.active_tasks: list[dict[str, Any]] = self._get_active_tasks()
        self.current_task: Task | None = self.get_current_task()  # Now expired_task exists when this is called

    def _get_task_data(self) -> dict[str, list[dict[str, Any]]]:
        try:
            with open(self.task_file, "r") as f:
                data = json.load(f)
            return data
        
        except Exception as e:
            logger.error(f"Error getting task data: {e}")
            return {}
    
    def _get_active_tasks(self) -> list[dict[str, Any]]:
        """
        Returns a list of Tasks from file that are active [today or future].
        """
        today = datetime.now().date()
        task_data = self._get_task_data()
        active_tasks = []

        def get_effective_time(task: Task) -> datetime:
            # Get the effective time by adding snooze_time (if any) to timestamp
            snooze_seconds = getattr(task, "snooze_time", 0)
            return task.timestamp + timedelta(seconds=snooze_seconds)

        for date_key, tasks_data in task_data.items():
            # Skip dates < today
            if datetime.strptime(date_key, "%Y-%m-%d").date() < today:
                continue

            # Convert dicts to Task objects
            tasks = [Task.to_class(task_dict) for task_dict in tasks_data]
            if tasks:
                # Sort tasks within each date group by effective time [earliest first]
                sorted_tasks = sorted(tasks, key=get_effective_time)

                active_tasks.append({
                    "date": sorted_tasks[0].get_date_str(),
                    "tasks": sorted_tasks
                })
        
        # Sort by date [earliest first]
        self._sort_tasks(active_tasks)
        if not active_tasks:
            start_task = self._get_start_task()
            active_tasks.append({
                "date": start_task.get_date_str(),
                "tasks": [start_task]
            })
        
        return active_tasks

    def _sort_tasks(self, tasks: list[dict[str, Any]]) -> None:
        """Sorts the active task groups by the first task's effective timestamp (timestamp + snooze_time)."""
        def get_effective_time(task):
            # Get the effective time by adding snooze_time (if any) to timestamp
            snooze_seconds = getattr(task, "snooze_time", 0)
            return task.timestamp + timedelta(seconds=snooze_seconds)

        tasks.sort(key=lambda x: get_effective_time(x["tasks"][0]) if x["tasks"] else datetime.max)
    
    def _get_start_task(self) -> Task:
        """Returns a start Task object."""
        return Task(timestamp=(datetime.now() - timedelta(minutes=1)).replace(second=0, microsecond=0),
                    message="No upcoming tasks!\nPress + to add a new one.",
                    expired=True)

    def get_current_task(self) -> Task | None:
        """Returns the first task that isn't expired and isn't the current expired task"""
        try:
            if not self.active_tasks:
                return None
            
            # Check all tasks to find the first one that isn't expired
            for active_task in self.active_tasks:
                for task in active_task["tasks"]:
                    # Skip if task is expired or is the current expired task
                    if task.expired or (self.expired_task and task.task_id == self.expired_task.task_id):
                        continue
                    return task

            return None

        except Exception as e:
            logger.error(f"Error checking task file: {e}")
            return None
    
    def refresh_current_task(self) -> None:
        """Refreshes the current task."""
        self.current_task = self.get_current_task()
    
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
    
    def handle_expired_task(self) -> Task | None:
        """Handles task expiration by setting it as the expired task and getting the next current task.
        Returns the expired task for notifications/alarms."""
        if not self.current_task:
            return None
            
        # Set as expired task (but don't mark as expired yet - wait for user action)
        self.expired_task = self.current_task
        logger.debug(f"Set task {self.expired_task.task_id} as expired task")
        
        # Get next current task
        self.current_task = self.get_current_task()
        
        return self.expired_task

    def snooze_task(self, action: str) -> None:
        """Snoozes the expired task or current task if no expired task exists."""
        task_to_snooze = self.expired_task or self.current_task
        if not task_to_snooze:
            logger.error("No task to snooze")
            return
            
        # Update snooze time but don't mark as expired
        snooze_seconds = 60 if action.endswith(ACTION.SNOOZE_A) else 120
        
        # Calculate the new timestamp after snooze
        new_timestamp = task_to_snooze.timestamp + timedelta(seconds=task_to_snooze.snooze_time + snooze_seconds)
        
        # Check for overlaps with other tasks
        if self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {task_to_snooze.task_id} would overlap with another task, adding 10 seconds")
            snooze_seconds += 10
        
        task_to_snooze.snooze_time += snooze_seconds
        
        # Save changes to file (only update snooze time)
        self._save_task_changes(task_to_snooze.task_id, {
            "snooze_time": task_to_snooze.snooze_time
        })
        
        logger.debug(f"Task {task_to_snooze.task_id} snoozed for {snooze_seconds/60:.1f} minutes ({snooze_seconds}s). Total snooze: {task_to_snooze.snooze_time/60:.1f}m")
        
        # If we snoozed an expired task, clear it
        if task_to_snooze == self.expired_task:
            self.expired_task = None
        
        # Refresh tasks from file and get new current task
        # The snoozed task will become current if its new time is earlier
        self.active_tasks = self._get_active_tasks()
        self.current_task = self.get_current_task()
    
    def _has_time_overlap(self, timestamp: datetime) -> bool:
        for task_group in self.active_tasks:
            for task in task_group["tasks"]:
                task_to_check = self.expired_task or self.current_task
                if task.task_id != task_to_check.task_id and not task.expired:
                    task_effective_time = task.timestamp + timedelta(seconds=task.snooze_time)
                    if abs((timestamp - task_effective_time).total_seconds()) < 1:  # If timestamps are within 1 second
                        return True
        
        return False

    def cancel_task(self) -> None:
        """Cancels the expired task if it exists, otherwise cancels current task."""
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
        
        # Refresh tasks and get new current task
        self.active_tasks = self._get_active_tasks()
        self.current_task = self.get_current_task()

        logger.debug(f"Cancelled task")

    def clear_expired_task(self) -> None:
        """Clears the expired task without saving changes."""
        if self.expired_task:
            logger.debug(f"Clearing expired task {self.expired_task.task_id}")
            self.expired_task = None

    def _save_task_changes(self, task_id: str, changes: dict) -> None:
        """Saves task changes to file"""
        try:
            task_data = self._get_task_data()
            for date_tasks in task_data.values():
                for task in date_tasks:
                    if task["task_id"] == task_id:
                        task.update(changes)
                        with open(self.task_file, "w") as f:
                            json.dump(task_data, f, indent=2)
                        logger.debug(f"Saved changes for task {task_id}: {changes}")
                        return
        except Exception as e:
            logger.error(f"Error saving task changes: {e}")
