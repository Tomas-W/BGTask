import json
import time

from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher

from src.managers.device_manager import DM
from src.managers.tasks.task_manager_utils import Task

from src.utils.logger import logger


from src.settings import PATH


class TaskManager(EventDispatcher):
    """
    Manages Tasks and their storage using JSON.
    """
    def __init__(self):
        super().__init__()
        self.navigation_manager = App.get_running_app().navigation_manager

        # Events
        self.register_event_type("on_task_saved_scroll_to_task")
        self.register_event_type("on_tasks_changed_update_task_display")
        self.register_event_type("on_task_edit_load_task_data")
        self.register_event_type("on_tasks_expired_set_date_expired")

        # File path
        self.task_file_path: str = DM.get_storage_path(PATH.TASK_FILE)
        DM.validate_file(self.task_file_path)

        # Tasks
        self.tasks_by_date: dict[str, list[Task]] = self._load_tasks_by_date()
        self.sorted_active_tasks: list[dict] = None

        # Editing
        self.selected_task_id: str | None = None
        # Date & Time
        self.selected_date: datetime | None = None
        self.selected_time: datetime | None = None
        # Vibration
        self.vibrate: bool = False
    
    def _load_tasks_by_date(self) -> dict[str, list[Task]] | dict:
        """
        Loads all Tasks from file, which are grouped by date.
        Returns a dictionary of date keys and lists of Task objects.
        """
        start_time = time.time()
        try:
            with open(self.task_file_path, "r") as f:
                data = json.load(f)
            
            tasks_by_date = {}
            for date_key, tasks_data in data.items():
                tasks_by_date[date_key] = []
                for task_data in tasks_data:
                    task = Task.to_class(task_data)
                    tasks_by_date[date_key].append(task)
            
            logger.trace(f"_load_tasks_by_date time: {time.time() - start_time:.4f}")
            return tasks_by_date
        
        except Exception as e:
            logger.error(f"Error initializing tasks: {e}")
            return {}
    
    def sort_active_tasks(self) -> None:
        """
        Takes the tasks_by_date dictionary and returns a list of Tasks sorted by date [earliest first].
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
        Returns True if successful, False otherwise.
        Called by save_all_tasks with a delay.
        Only called on Task add/edit/delet.
        """
        start_time = time.time()
        try:
            tasks_json = {}
            # Group by date
            for date_key, tasks in self.tasks_by_date.items():
                tasks_json[date_key] = [task.to_json() for task in tasks]
            
            with open(self.task_file_path, "w") as f:
                json.dump(tasks_json, f, indent=2)
            logger.trace(f"save_tasks_to_json time: {time.time() - start_time:.4f}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving tasks to file: {e}")
            return False
    
    def save_tasks_to_json(self) -> None:
        """
        Saves all Tasks to the PATH.TASK_FILE file, grouped by date.
        Called by add_task, update_task, and delete_task with a delay.
        """
        Clock.schedule_once(self._save_tasks_to_json, 0.2)
    
    def add_task(self, message: str, timestamp: datetime,
                 alarm_name: str, vibrate: bool) -> None:
        """
        Adds Task to tasks_by_date, saves the Task to file,
         dispatches an event to update the Task display and scroll to the Task.
        """
        task = Task(message=message, timestamp=timestamp,
                    alarm_name=alarm_name, vibrate=vibrate)
        
        # Get date key and add to appropriate date group
        date_key = task.get_date_key()
        if date_key not in self.tasks_by_date:
            self.tasks_by_date[date_key] = []
        
        # Save
        self.tasks_by_date[date_key].append(task)
        self.save_tasks_to_json()

        # Notify to update the Task display
        self.dispatch("on_tasks_changed_update_task_display", modified_task=task)
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved_scroll_to_task", task=task), 0.1)
    
    def update_task(self, task_id: str, message: str,
                    timestamp: datetime, alarm_name: str, vibrate: bool) -> None:
        """
        Updates existing Task by its ID.
        Updates tasks_by_date, saves the Task to file,
         dispatches an event to update the Task display and scroll to the Task.
        """
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
        
        # Update expired state
        now = datetime.now()
        if timestamp > now and task.expired:
            # Task from past to future, -> not expired
            task.expired = False
        elif timestamp <= now and not task.expired:
            # Task from future to past, -> expired
            task.expired = True
        
        new_date_key = task.get_date_key()
        
        # If date changed, move Task to new date group
        if old_date_key != new_date_key:
            # Remove from old date group
            if old_date_key in self.tasks_by_date:
                self.tasks_by_date[old_date_key].remove(task)
                # Remove empty date groups
                if not self.tasks_by_date[old_date_key]:
                    del self.tasks_by_date[old_date_key]
            
            # Add to new date group
            if new_date_key not in self.tasks_by_date:
                self.tasks_by_date[new_date_key] = []
            self.tasks_by_date[new_date_key].append(task)

        self.save_tasks_to_json()
        # Notify to update the Task display
        self.dispatch("on_tasks_changed_update_task_display", modified_task=task)
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved_scroll_to_task", task=task), 0.1)

    def delete_task(self, task_id: str) -> None:
        """
        Deletes a Task by ID.
        Updates tasks_by_date, saves the Task to file,
         dispatches an event to update the Task display.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        # Save copy before deletion for notification
        date_key = task.get_date_key()
        task_copy = Task(
            task_id=task.task_id,
            message=task.message,
            timestamp=task.timestamp,
            alarm_name=task.alarm_name,
            vibrate=task.vibrate,
            expired=task.expired
        )
        
        # Remove from memory
        if date_key in self.tasks_by_date and task in self.tasks_by_date[date_key]:
            self.tasks_by_date[date_key].remove(task)
            # Remove empty date groups
            if not self.tasks_by_date[date_key]:
                del self.tasks_by_date[date_key]
        
        self.save_tasks_to_json()
        # Notify to update Task display
        self.dispatch("on_tasks_changed_update_task_display", modified_task=task_copy)

    def set_expired_tasks(self) -> None:
        """
        Set Tasks to be expired if their timestamp is in the past.
        Checks first active Task group and sets each Tasks expired state.
        If changes, save to memory and file.
        If all Tasks in group are now expired, notify to update Task's appearance.
        """
        now = datetime.now()
        active_tasks = self.sorted_active_tasks[0]
        if not active_tasks:
            return
        
        # Check each Task for expired state
        changed = False
        for task in active_tasks["tasks"]:
            if task.timestamp < now and not task.expired:
                task.expired = True
                changed = True
                logger.debug(f"Task {task.timestamp.strftime('%H:%M')} set to expired")
        
        if changed:
            self.save_tasks_to_json()
            if all(task.expired for task in active_tasks["tasks"]):
                self.dispatch("on_tasks_expired_set_date_expired", 
                                      date=active_tasks["date"])
    
    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a Task object by its ID."""
        for date_key, tasks in self.tasks_by_date.items():
            for task in tasks:
                if task.task_id == task_id:
                    return task
        
        return None
    
    def on_task_saved_scroll_to_task(self, task, *args):
        """Default handler for on_task_saved_scroll_to_task event"""
        pass
    
    def on_tasks_changed_update_task_display(self, *args, **kwargs):
        """Default handler for on_tasks_changed_update_task_display event"""
        pass
    
    def on_task_edit_load_task_data(self, *args, **kwargs):
        """Default handler for on_task_edit_load_task_data event"""
        pass
    
    def on_tasks_expired_set_date_expired(self, *args, **kwargs):
        """Default handler for on_tasks_expired_set_date_expired event"""
        pass
