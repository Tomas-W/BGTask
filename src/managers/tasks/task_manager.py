import json
import time

from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher

from src.managers.tasks.task_manager_utils import Task

from src.utils.logger import logger
from src.utils.platform import get_storage_path, validate_file


from src.settings import PATH, SCREEN


class TaskManager(EventDispatcher):
    """
    Manages Tasks and their storage using JSON files.
    Maintains two files:
    - tasks.json: Stores all Tasks grouped by date.
    """
    def __init__(self):
        super().__init__()
        self.navigation_manager = App.get_running_app().navigation_manager

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
        
        # Initialize storage files
        self.task_file: str = get_storage_path(PATH.TASK_FILE)
        validate_file(self.task_file)

        # Tasks storage by date
        self.tasks_by_date = {}  # Dictionary with date keys and list of tasks as values
        
        # Track data changes
        self.data_changed = False
        
        # Load Tasks from file
        self._init_tasks()
    
    def _init_tasks(self) -> None:
        """
        Load tasks from file and organize them by date.
        """
        try:
            with open(self.task_file, "r") as f:
                data = json.load(f)
            
            self.tasks_by_date = {}
            
            # If the data is already in date-grouped format
            if isinstance(data, dict):
                for date_key, tasks_data in data.items():
                    self.tasks_by_date[date_key] = []
                    for task_data in tasks_data:
                        task = Task.to_class(task_data)
                        self.tasks_by_date[date_key].append(task)
            else:
                logger.error("INVALID DATA FORMAT")
        
        except Exception as e:
            logger.error(f"Error initializing tasks: {e}")
            raise e

    def _get_first_task_date(self) -> datetime:
        """
        Returns the date of the first active Task.
        Returns today's date if there are tasks for today (even expired ones).
        Returns the earliest date with non-expired tasks otherwise.
        If no tasks exist, returns today's date.
        """
        if not self.tasks_by_date:
            return datetime.now().date()
        
        today = datetime.now().date()
        today_key = today.isoformat()
        
        # If there are tasks for today, return today's date regardless of expired status
        if today_key in self.tasks_by_date and self.tasks_by_date[today_key]:
            return today
            
        # Get all date keys and sort them chronologically
        sorted_date_keys = sorted(self.tasks_by_date.keys())
        if not sorted_date_keys:
            return today
        
        # Try to find the earliest date with non-expired tasks
        for date_key in sorted_date_keys:
            tasks = self.tasks_by_date[date_key]
            
            # Find the earliest non-expired task
            non_expired_tasks = [task for task in tasks if not task.expired]
            if non_expired_tasks:
                # Return the date of the earliest non-expired task
                sorted_tasks = sorted(non_expired_tasks, key=lambda t: t.timestamp)
                return sorted_tasks[0].timestamp.date()
        
        # If all tasks are expired, return the earliest date
        earliest_date_key = sorted_date_keys[0]
        return datetime.fromisoformat(earliest_date_key).date()
    
    def get_sorted_tasks(self) -> list[dict]:
        """Returns a list of Tasks sorted by date [earliest first]."""
        result = []
        
        # Sort the date keys chronologically
        sorted_date_keys = sorted(self.tasks_by_date.keys())
        
        for date_key in sorted_date_keys:
            tasks = self.tasks_by_date[date_key]
            
            # Always include all tasks for all dates
            if tasks:
                # Sort tasks within each date group by time (earliest first)
                sorted_tasks = sorted(tasks, key=lambda task: task.timestamp)
                
                # Get formatted date string for display
                date_str = sorted_tasks[0].get_date_str() if sorted_tasks else ""
                
                result.append({
                    "date": date_str,
                    "tasks": sorted_tasks
                })
        
        # Sort the whole result by earliest date
        result.sort(key=lambda x: x["tasks"][0].timestamp if x["tasks"] else datetime.max)
        return result

    def _save_tasks_to_json(self, modified_task: Task = None) -> bool:
        """Saves all Tasks to the PATH.TASK_FILE file, grouped by date."""
        try:
            # Convert tasks to JSON format
            tasks_json = {}
            
            # Process all tasks grouped by date
            for date_key, tasks in self.tasks_by_date.items():
                tasks_json[date_key] = [task.to_json() for task in tasks]
            
            with open(self.task_file, "w") as f:
                json.dump(tasks_json, f, indent=2)
            return True
        
        except Exception as e:
            logger.error(f"Error saving tasks to file: {e}")
            return False
    
    def save_all_tasks(self) -> bool:
        """
        Save all tasks to file. Should be called on app exit or for occasional backups.
        """
        success = self._save_tasks_to_json()
        if success:
            self.data_changed = False
        return success
    
    def add_task(self, message: str, timestamp: datetime,
                 alarm_name: str, vibrate: bool) -> None:
        """Add a new Task to storage and tasks list."""
        task = Task(message=message, timestamp=timestamp,
                    alarm_name=alarm_name, vibrate=vibrate)
        
        # Get date key and add to appropriate date group
        date_key = task.get_date_key()
        if date_key not in self.tasks_by_date:
            self.tasks_by_date[date_key] = []
        
        self.tasks_by_date[date_key].append(task)
        
        # Mark data as changed
        self.data_changed = True
        
        # Notify UI to update
        self.dispatch("on_tasks_changed")
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)
    
    def edit_task(self, task_id: str) -> None:
        """
        Edit an existing task by ID.
        Copy Task data to NewTaskScreen and navigate to it.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        # Notify to load data into NewTaskScreen
        self.dispatch("on_task_edit", task=task)
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
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
        
        # Mark data as changed
        self.data_changed = True
        
        logger.debug(f"Updated task: {task_id}")
        self.dispatch("on_tasks_changed")
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        date_key = task.get_date_key()
        
        # Remove from date-grouped storage
        if date_key in self.tasks_by_date and task in self.tasks_by_date[date_key]:
            self.tasks_by_date[date_key].remove(task)
            # Clean up empty date groups
            if not self.tasks_by_date[date_key]:
                del self.tasks_by_date[date_key]
        
        # Mark data as changed
        self.data_changed = True
        
        logger.debug(f"Deleted task: {task_id}")
        # Notify to update task display
        self.dispatch("on_tasks_changed")

    def set_expired_tasks(self):
        """Set the expired tasks."""
        now = datetime.now()
        changed = False
        
        # Check all tasks in all date groups
        for date_key, tasks in self.tasks_by_date.items():
            for task in tasks:
                if task.timestamp < now and not task.expired:
                    task.expired = True
                    changed = True
        
        if changed:
            # Mark data as changed
            self.data_changed = True
            self.dispatch("on_tasks_changed")
    
    def get_task_by_id(self, task_id: str) -> Task:
        """Get a task by its ID from memory."""
        # Search through all tasks by date
        for date_key, tasks in self.tasks_by_date.items():
            for task in tasks:
                if task.task_id == task_id:
                    return task
        
        return None
    
    def on_task_saved(self, task, *args):
        """Default handler for on_task_saved event"""
        logger.debug(f"on_task_saved event finished: {task}")
    
    def on_tasks_changed(self, *args):
        """Default handler for on_tasks_changed event"""
        logger.debug("on_tasks_changed event finished")
    
    def on_task_edit(self, task, *args):
        """Default handler for on_task_edit event"""
        logger.debug("on_task_edit event finished")
    