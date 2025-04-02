import json

from datetime import datetime

from kivy.app import App
from kivy.event import EventDispatcher

from src.managers.tasks.task_manager_utils import Task

from src.utils.logger import logger
from src.utils.platform import get_storage_path, validate_file

from src.settings import PATH, SCREEN


class TaskManager(EventDispatcher):
    """
    Manages Tasks and their storage.
    """
    def __init__(self):
        super().__init__()        
        self.navigation_manager = App.get_running_app().navigation_manager
        self.register_event_type("on_tasks_changed")
        
        self.task_file = get_storage_path(PATH.TASK_FILE)
        validate_file(self.task_file)
        self.tasks = self.load_tasks()
    
    def on_tasks_changed(self, *args):
        """Default handler for on_tasks_changed event"""
        logger.debug("on_tasks_changed event finished")
    
    def load_tasks(self) -> list[Task]:
        """Load Tasks from task_file."""
        try:
            with open(self.task_file, "r") as f:
                task_data = json.load(f)
            
            tasks = [Task.from_dict(data) for data in task_data]
            # Sort tasks by timestamp
            tasks.sort(key=lambda task: task.timestamp)
            logger.debug(f"Loaded {len(tasks)} tasks")
            return tasks
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing task file: {e}")
            return []
        except FileNotFoundError:
            logger.warning(f"Task file not found: {self.task_file}")
            return []
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return []
    
    def add_task(self, message: str, timestamp: datetime, alarm_name: str) -> None:
        """Add a new Task to self.tasks and save to task_file."""
        task = Task(message=message, timestamp=timestamp, alarm_name=alarm_name)
        self.tasks.append(task)
        self._save_tasks()
        # Notify listeners that tasks have changed
        self.dispatch("on_tasks_changed")
    
    def _save_tasks(self) -> None:
        """Save Tasks to task_file."""
        try:
            task_data = [task.to_dict() for task in self.tasks]
            with open(self.task_file, "w") as f:
                json.dump(task_data, f, indent=2)
            logger.debug("Saved tasks to task_file")
        
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def edit_task(self, task_id: str) -> None:
        """
        Edit an existing task by ID.
        Copy Task data to NewTaskScreen and navigate to it.
        """
        task = next((task for task in self.tasks if task.task_id == task_id), None)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        new_task_screen = App.get_running_app().get_screen(SCREEN.NEW_TASK)
        new_task_screen.load_task_data(task)
        
        # Navigate to the edit screen
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
    def update_task(self, task_id: str, message: str,
                    timestamp: datetime, alarm_name: str) -> None:
        """Update an existing Task by its ID."""
        task = next((task for task in self.tasks if task.task_id == task_id), None)
        if not task:
            logger.error(f"Task with id {task_id} not found for update")
            return
        
        # Update the task
        task.timestamp = timestamp
        task.message = message
        task.alarm_name = alarm_name
        logger.debug(f"Updated task: {task_id}")
        
        # Save changes
        self._save_tasks()

        # Notify listeners
        self.dispatch("on_tasks_changed")

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        task = next((task for task in self.tasks if task.task_id == task_id), None)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
            
        # Remove task and save task_file
        self.tasks.remove(task)
        logger.debug(f"Deleted task: {task_id}")
        self._save_tasks()
        
        # Notify listeners that tasks have changed
        self.dispatch("on_tasks_changed")

    def get_tasks_by_dates(self) -> list[dict]:
        """Group Tasks by date."""
        tasks_by_date = {}
        for task in self.tasks:
            date_str = task.get_date_str()

            if date_str not in tasks_by_date:
                tasks_by_date[date_str] = []

            tasks_by_date[date_str].append(task)
        
        result = []
        for date, tasks in tasks_by_date.items():
            # Sort tasks within each date group by time (earliest first)
            sorted_tasks = sorted(tasks, key=lambda task: task.timestamp)
            result.append({
                "date": date,
                "tasks": sorted_tasks
            })
        
        # Sort the result by the earliest task in each group
        result.sort(key=lambda x: x["tasks"][0].timestamp if x["tasks"] else datetime.max)
        
        return result 
