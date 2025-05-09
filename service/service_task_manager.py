import json
import os
from datetime import datetime, timedelta
from typing import Any

from src.managers.tasks.task_manager_utils import Task
from service.utils import PATH, ACTION


class ServiceTaskManager:
    def __init__(self):
        self.task_file: str = PATH.TASK_FILE
        self.active_tasks: list[dict[str, Any]] = self._get_active_tasks()
        self.current_task: Task | None = self.get_current_task()
        self.snooze_time: int = 0

    def _get_task_data(self) -> dict[str, list[dict[str, Any]]]:
        try:
            with open(self.task_file, "r") as f:
                data = json.load(f)
            return data
        
        except Exception as e:
            print(f"Error getting task data: {e}")
            return {}
    
    def _get_active_tasks(self) -> list[dict[str, Any]]:
        """
        Returns a list of Tasks from file that are active [today or future].
        """
        today = datetime.now().date()
        task_data = self._get_task_data()
        active_tasks = []

        for date_key, tasks_data in task_data.items():
            # Skip dates < today
            if datetime.strptime(date_key, "%Y-%m-%d").date() < today:
                continue

            # Convert dicts to Task objects
            tasks = [Task.to_class(task_dict) for task_dict in tasks_data]
            if tasks:
                # Sort tasks within each date group by time [earliest first]
                sorted_tasks = sorted(tasks, key=lambda task: task.timestamp)

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
        """Sorts the active task groups by the first task's timestamp."""
        tasks.sort(key=lambda x: x["tasks"][0].timestamp if x["tasks"] else datetime.max)
    
    def _get_start_task(self) -> Task:
        """Returns a start Task object."""
        return Task(timestamp=(datetime.now() - timedelta(minutes=1)).replace(second=0, microsecond=0),
                    message="No upcoming tasks!\nPress + to add a new one.",
                    expired=True)

    def get_current_task(self) -> Task | None:
        """
        Returns the first active Task from the active_tasks list.
        """
        try:
            if not self.active_tasks:
                return None
            
            for active_task in self.active_tasks:
                first_task = active_task["tasks"][0]
                if first_task.timestamp > datetime.now():
                    return first_task

            return None

        except Exception as e:
            print(f"BGTaskService: Error checking task file: {e}")
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
            trigger_time = task_time + timedelta(seconds=self.snooze_time)
            return datetime.now() >= trigger_time
        
        except Exception as e:
            print(f"BGTaskService: Error parsing timestamp: {e}")
            return False
    
    def snooze_task(self, action: str) -> None:
        """Snoozes the current task for 1 minute."""
        if action.endswith(ACTION.SNOOZE_A):
            # Snooze for 1 minute
            self.snooze_time += 1 * 60
            print(f"BGTaskService: Task snoozed for 1 minute. Total snooze: {self.snooze_time/60:.1f}m")
        
        elif action.endswith(ACTION.SNOOZE_B):
            # Snooze for 2 minutes
            self.snooze_time += 2 * 60
            print(f"BGTaskService: Task snoozed for 2 minutes. Total snooze: {self.snooze_time/60:.1f}m")
        
        else:
            print(f"BGTaskService: Invalid snooze action: {action}")
    
    def cancel_task(self) -> None:
        """Cancels the current task."""
        self.current_task = None
        self.snooze_time = 0
        print("BGTaskService: Task cancelled")
