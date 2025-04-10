import json

from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher

from src.managers.tasks.task_manager_utils import Task

from src.utils.logger import logger
from src.utils.misc import get_storage_path, validate_file


from src.settings import PATH, SCREEN


class TaskManager(EventDispatcher):
    """
    Manages Tasks and their storage using JSON.
    """
    def __init__(self):
        super().__init__()
        self.navigation_manager = App.get_running_app().navigation_manager

        # File path
        self.task_file_path: str = get_storage_path(PATH.TASK_FILE)
        validate_file(self.task_file_path)

        # Tasks
        self.tasks_by_date: dict[str, list[Task]] = self._load_tasks_by_date()
        self.sorted_active_tasks: list[dict] = None

        # Events
        self.register_event_type("on_task_saved")
        self.register_event_type("on_tasks_changed")
        self.register_event_type("on_task_edit")

        # Editing
        self.selected_task_id: str | None = None
        # Date & Time
        self.selected_date: datetime | None = None
        self.selected_time: datetime | None = None
        # Vibration
        self.vibrate: bool = False
    
    def _load_tasks_by_date(self) -> dict[str, list[Task]]:
        """
        Load all Tasks from file, which are grouped by date.
        Takes a JSON file and returns a dictionary of date keys and lists of Task objects.
        """
        try:
            with open(self.task_file_path, "r") as f:
                data = json.load(f)
            
            tasks_by_date = {}
            for date_key, tasks_data in data.items():
                tasks_by_date[date_key] = []
                for task_data in tasks_data:
                    task = Task.to_class(task_data)
                    tasks_by_date[date_key].append(task)
            
            return tasks_by_date
        
        except Exception as e:
            logger.error(f"Error initializing tasks: {e}")
            return {}
    
    def sort_active_tasks(self) -> None:
        """
        Returns a list of Tasks sorted by date [earliest first].
        Only includes tasks from today or future dates [active].
        Used by HomeScreen's update_task_display to display all active Tasks.
        Only called on initial load and after Task add/edit/delete.
        """
        sorted_active_tasks = []
        today = datetime.now().date()
        
        for date_key in self.tasks_by_date.keys():
            # Skip dates that are earlier than today
            if datetime.strptime(date_key, "%Y-%m-%d").date() < today:
                continue
            
            tasks = self.tasks_by_date[date_key]
            current_tasks = [task for task in tasks]
            
            if current_tasks:
                # Sort tasks within each date group by time (earliest first)
                sorted_tasks = sorted(current_tasks, key=lambda task: task.timestamp)
                
                sorted_active_tasks.append({
                    "date": sorted_tasks[0].get_date_str(),
                    "tasks": sorted_tasks
                })
        
        # Sort by date (earliest first)
        sorted_active_tasks.sort(key=lambda x: x["tasks"][0].timestamp if x["tasks"] else datetime.max)
        self.sorted_active_tasks = sorted_active_tasks

    def _save_tasks_to_json(self, modified_task: Task = None) -> bool:
        """
        Saves all Tasks to the PATH.TASK_FILE file, grouped by date.
        Called by save_all_tasks with a delay.
        Only called on Task add/edit/delet.
        """
        try:
            tasks_json = {}
            # Group by date
            for date_key, tasks in self.tasks_by_date.items():
                tasks_json[date_key] = [task.to_json() for task in tasks]
            
            with open(self.task_file_path, "w") as f:
                json.dump(tasks_json, f, indent=2)
            return True
        
        except Exception as e:
            logger.error(f"Error saving tasks to file: {e}")
            return False
    
    def save_tasks_to_json(self):
        """
        Save all Tasks to the PATH.TASK_FILE file, grouped by date.
        Called by add_task, update_task, and delete_task with a delay.
        """
        Clock.schedule_once(self._save_tasks_to_json, 0.2)
    
    def add_task(self, message: str, timestamp: datetime,
                 alarm_name: str, vibrate: bool) -> None:
        """Add a new Task to file and memory."""
        task = Task(message=message, timestamp=timestamp,
                    alarm_name=alarm_name, vibrate=vibrate)
        
        # Get date key and add to appropriate date group
        date_key = task.get_date_key()
        if date_key not in self.tasks_by_date:
            self.tasks_by_date[date_key] = []
        
        self.tasks_by_date[date_key].append(task)
        self.save_tasks_to_json()

        # Notify UI to update the Task display
        self.dispatch("on_tasks_changed", modified_task=task)
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)
    
    def update_task(self, task_id: str, message: str,
                    timestamp: datetime, alarm_name: str, vibrate: bool) -> None:
        """Update an existing Task by its ID."""
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found for update")
            return
        
        old_date_key = task.get_date_key()
        
        # Update task properties
        task.timestamp = timestamp
        task.message = message
        task.alarm_name = alarm_name
        task.vibrate = vibrate
        
        new_date_key = task.get_date_key()
        
        # Check if the date has changed, and move the task to the new date group if needed
        if old_date_key != new_date_key:
            # Remove from old date group
            if old_date_key in self.tasks_by_date:
                self.tasks_by_date[old_date_key].remove(task)
                # Clean up empty date groups
                if not self.tasks_by_date[old_date_key]:
                    del self.tasks_by_date[old_date_key]
            
            # Add to new date group
            if new_date_key not in self.tasks_by_date:
                self.tasks_by_date[new_date_key] = []
            self.tasks_by_date[new_date_key].append(task)

        self.save_tasks_to_json()

        logger.debug(f"Updated task: {task_id}")
        # Notify UI to update with specific task
        self.dispatch("on_tasks_changed", modified_task=task)
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        # Save a copy of the task before deletion for notification
        date_key = task.get_date_key()
        date_str = task.get_date_str()
        task_copy = Task(
            task_id=task.task_id,
            message=task.message,
            timestamp=task.timestamp,
            alarm_name=task.alarm_name,
            vibrate=task.vibrate,
            expired=task.expired
        )
        
        # Remove from date-grouped storage
        if date_key in self.tasks_by_date and task in self.tasks_by_date[date_key]:
            self.tasks_by_date[date_key].remove(task)
            # Clean up empty date groups
            if not self.tasks_by_date[date_key]:
                del self.tasks_by_date[date_key]
        
        self.save_tasks_to_json()

        logger.debug(f"Deleted task: {task_id}")
        # Notify to update task display with the original task information
        self.dispatch("on_tasks_changed", modified_task=task_copy)

    def set_expired_tasks(self):
        """Set Task to be expired if its timestamp is in the past."""
        now = datetime.now()
        modified_tasks = []
        
        for date_key, tasks in self.tasks_by_date.items():
            for task in tasks:
                if task.timestamp < now and not task.expired:
                    task.expired = True
                    modified_tasks.append(task)
        
        if modified_tasks:
            # If many tasks changed, do a full rebuild
            if len(modified_tasks) > 3:
                self.dispatch("on_tasks_changed")
            else:
                # Otherwise, update each task individually
                for task in modified_tasks:
                    self.dispatch("on_tasks_changed", modified_task=task)
            self.save_tasks_to_json()
    
    def get_task_by_id(self, task_id: str) -> Task:
        """Get a Task by its ID."""
        # Search through all tasks by date
        for date_key, tasks in self.tasks_by_date.items():
            for task in tasks:
                if task.task_id == task_id:
                    return task
        
        return None
    
    def on_task_saved(self, task, *args):
        """Default handler for on_task_saved event"""
        logger.debug(f"on_task_saved event finished: {task}")
    
    def on_tasks_changed(self, *args, **kwargs):
        """Default handler for on_tasks_changed event"""
        logger.debug("on_tasks_changed event finished")
    
    def on_task_edit(self, *args, **kwargs):
        """Default handler for on_task_edit event"""
        logger.debug("on_task_edit event finished")
