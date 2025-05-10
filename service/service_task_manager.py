import json

from datetime import datetime, timedelta
from typing import Any

from src.managers.tasks.task_manager_utils import Task

from service.service_logger import logger
from service.utils import PATH, ACTION


class ServiceTaskManager:
    def __init__(self):
        self.task_file: str = PATH.TASK_FILE
        self.monitoring_tasks: set[str] = set()
        self.active_tasks: list[dict[str, Any]] = self._get_active_tasks()
        self.current_task: Task | None = self.get_current_task()

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
        """Returns the first task that isn't being monitored and isn't expired"""
        try:
            if not self.active_tasks:
                return None
            
            # Check all tasks to find the first one that isn't being monitored and isn't expired
            for active_task in self.active_tasks:
                for task in active_task["tasks"]:
                    # Skip if task is already being monitored or is expired
                    if task.task_id in self.monitoring_tasks or task.expired:
                        continue
                    logger.debug(f"Selected task {task.task_id}")
                    return task

            logger.debug("No tasks found")
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
    
    def snooze_task(self, action: str) -> None:
        """Snoozes the current task for 1 minute."""
        if action.endswith(ACTION.SNOOZE_A):
            # Snooze for 1 minute
            self.current_task.snooze_time += 1 * 60
            self._snooze_task(ACTION.SNOOZE_A)
            # Remove from monitoring since we're snoozing it
            if self.current_task:
                self.monitoring_tasks.discard(self.current_task.task_id)
            logger.debug(f"Task snoozed for 1 minute. Total snooze: {self.current_task.snooze_time/60:.1f}m")
        
        elif action.endswith(ACTION.SNOOZE_B):
            # Snooze for 2 minutes
            self.current_task.snooze_time += 2 * 60
            self._snooze_task(ACTION.SNOOZE_B)
            # Remove from monitoring since we're snoozing it
            if self.current_task:
                self.monitoring_tasks.discard(self.current_task.task_id)
            logger.debug(f"Task snoozed for 2 minutes. Total snooze: {self.current_task.snooze_time/60:.1f}m")
        
        else:
            logger.error(f"Invalid snooze action: {action}")
    
    def _snooze_task(self, action: str) -> None:
        """Updates task's snooze time in memory and file, then refreshes tasks"""
        try:
            if not self.current_task:
                return
            
            # Get current task data from file to ensure we have latest
            task_data = self._get_task_data()
            
            # Find and update the task in the data
            for date_tasks in task_data.values():
                for task in date_tasks:
                    if task["task_id"] == self.current_task.task_id:
                        # Initialize snooze_time if it doesn't exist
                        if "snooze_time" not in task:
                            task["snooze_time"] = 0
                        
                        # Add snooze time based on action
                        snooze_seconds = 60 if action == ACTION.SNOOZE_A else 120
                        task["snooze_time"] += snooze_seconds
                        
                        # Save updated data back to file
                        with open(self.task_file, "w") as f:
                            json.dump(task_data, f, indent=2)
                        
                        logger.debug(f"Updated task {task['task_id']} snooze_time to {task['snooze_time']} seconds")
                        break
            
            # Refresh tasks from file
            self.active_tasks = self._get_active_tasks()
            self.current_task = self.get_current_task()
            
        except Exception as e:
            logger.error(f"Error updating task snooze time: {e}")
    
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

    def cancel_task(self) -> None:
        """Cancels the current task."""
        if self.current_task:
            # Mark as expired and remove from monitoring
            self.current_task.expired = True
            self.monitoring_tasks.discard(self.current_task.task_id)
            logger.debug(f"Task {self.current_task.task_id} cancelled and marked as expired")
            
            # Save changes to file
            self._save_task_changes(self.current_task.task_id, {"expired": True})
        
        self.active_tasks = self._get_active_tasks()
        self.current_task = self.get_current_task()

    def handle_expired_task(self) -> None:
        """Adds the current task to monitoring and gets the next task"""
        if self.current_task:
            self.monitoring_tasks.add(self.current_task.task_id)
            logger.debug(f"Added task {self.current_task.task_id} to monitoring")
            
            # Save changes to file
            self._save_task_changes(self.current_task.task_id, {"expired": True})
            
            self.current_task = self.get_current_task()

    def clear_monitoring(self) -> None:
        """Clears the monitoring tasks set"""
        self.monitoring_tasks.clear()
        logger.debug("Cleared monitoring tasks")
