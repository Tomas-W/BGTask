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
        
        # Init storage file
        self.task_file: str = get_storage_path(PATH.TASK_FILE)
        validate_file(self.task_file)

        # Tasks storage by date
        self.tasks_by_date: dict[str, list[Task]] = self._load_tasks_by_date()
    
    def _load_tasks_by_date(self) -> dict[str, list[Task]]:
        """
        Load Tasks from file, grouped by date.
        """
        try:
            with open(self.task_file, "r") as f:
                data = json.load(f)
            
            tasks_by_date = {}
            if isinstance(data, dict):
                for date_key, tasks_data in data.items():
                    tasks_by_date[date_key] = []
                    for task_data in tasks_data:
                        task = Task.to_class(task_data)
                        tasks_by_date[date_key].append(task)
                
                return tasks_by_date
            
            else:
                logger.error("INVALID DATA FORMAT")
                return {}
        
        except Exception as e:
            logger.error(f"Error initializing tasks: {e}")
            return {}

    def _get_first_task_date(self) -> datetime:
        """
        Returns the date of the first active Task.
        Priority:
        1. Today's date if there are Tasks for today
        2. The earliest future date with Tasks
        3. Today's date if no Tasks exist
        """
        if not self.tasks_by_date:
            return datetime.now().date()
        
        today = datetime.now().date()
        today_key = today.isoformat()
        
        # Check today's Tasks
        if today_key in self.tasks_by_date and self.tasks_by_date[today_key]:
            return today
        
        # Sort all dates
        sorted_date_keys = sorted(self.tasks_by_date.keys())
        
        # Find first future date
        for date_key in sorted_date_keys:
            date = datetime.fromisoformat(date_key).date()
            if date >= today:
                return date
        
        # Fallback to today
        return today
    
    def get_sorted_tasks(self) -> list[dict]:
        """
        Returns a list of Tasks sorted by date [earliest first].
        Used by StartScreen to display all active Tasks.
        """
        result = []
        
        # Sort by date
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
            tasks_json = {}
            
            # Group by date
            for date_key, tasks in self.tasks_by_date.items():
                tasks_json[date_key] = [task.to_json() for task in tasks]
            
            with open(self.task_file, "w") as f:
                json.dump(tasks_json, f, indent=2)
            return True
        
        except Exception as e:
            logger.error(f"Error saving tasks to file: {e}")
            return False
    
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

        # Save to file
        self._save_tasks_to_json()

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

        # Save to file
        self._save_tasks_to_json()

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
        
        # Save to file
        self._save_tasks_to_json()

        logger.debug(f"Deleted task: {task_id}")
        # Notify to update task display
        self.dispatch("on_tasks_changed")

    def set_expired_tasks(self):
        """Set Task to be expired if its timestamp is in the past."""
        now = datetime.now()
        changed = False
        
        # Check all tasks in all date groups
        for date_key, tasks in self.tasks_by_date.items():
            for task in tasks:
                if task.timestamp < now and not task.expired:
                    task.expired = True
                    changed = True
        
        if changed:
            self.dispatch("on_tasks_changed")
    
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
    
    def on_tasks_changed(self, *args):
        """Default handler for on_tasks_changed event"""
        logger.debug("on_tasks_changed event finished")
    
    def on_task_edit(self, task, *args):
        """Default handler for on_task_edit event"""
        logger.debug("on_task_edit event finished")
    