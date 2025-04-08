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
    - tasks.json: stores all tasks
    - first_task.json: stores today's or nearest future tasks for quick startup
    """
    def __init__(self):
        super().__init__()
        self.navigation_manager = App.get_running_app().navigation_manager

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
        self.tasks_file = get_storage_path(PATH.TASK_FILE)
        self.first_task_file = get_storage_path(PATH.FIRST_TASK)
        validate_file(self.tasks_file)
        validate_file(self.first_task_file)
        
        self.first_task = self._get_first_task()
        self.active_tasks = self._get_active_tasks()
        self.expired_tasks = self._get_expired_tasks()

    def _get_first_task_date(self) -> datetime:
        """Get the date of the first task."""
        return self.first_task[0].timestamp.date()
    
    def _get_first_task(self) -> list[Task]:
        """Load the first expiring Tasks."""
        start_time = time.time()
        try:
            with open(self.tasks_file, "r") as f:
                all_task_data = json.load(f)
            
            today = datetime.now().date()
            today_tasks = []
            
            for task_data in all_task_data:
                task = Task.from_dict(task_data)
                if task.timestamp.date() == today:
                    today_tasks.append(task)
            
            end_time = time.time()
            logger.error(f"TaskManager load_first_task time: {end_time - start_time}")
            return today_tasks
        except Exception as e:
            logger.error(f"Error loading today's tasks: {e}")
            return []
    
    def _update_first_task_file(self) -> None:
        """
        Updates the first_task_file.json with the earliest tasks.
        This makes the StartScreen load faster as it only needs to read the minimal set of tasks.
        """
        start_time = time.time()
        try:
            if not self.active_tasks:
                # No tasks, write empty list
                with open(self.first_task_file, "w") as f:
                    json.dump([], f, indent=2)
                return
            
            # Get earliest date and its tasks
            earliest_tasks = []
            earliest_date = self.active_tasks[0].timestamp.date()  # Tasks are already sorted
            
            for task in self.active_tasks:
                if task.timestamp.date() == earliest_date:
                    earliest_tasks.append(task.to_dict())
                else:
                    break  # Stop once we hit a different date
            
            # Update first_task
            self.first_task = earliest_tasks
            
            # Write to file
            with open(self.first_task_file, "w") as f:
                json.dump(earliest_tasks, f, indent=2)
            
            end_time = time.time()
            logger.error(f"TaskManager update_first_task_file time: {end_time - start_time}")
        
        except Exception as e:
            logger.error(f"Error updating first_task_file.json: {e}")
    
    def _get_active_tasks(self) -> list[Task]:
        """Load all Tasks from file that are from today or in the future."""
        start_time = time.time()
        try:
            with open(self.tasks_file, "r") as f:
                task_data = json.load(f)
            
            today = datetime.now().date()
            # First convert to Task objects, then filter
            tasks = [Task.from_dict(data) for data in task_data]
            active_tasks = [task for task in tasks if task.timestamp.date() >= today]
            
            # Sort tasks by timestamp
            active_tasks.sort(key=lambda task: task.timestamp)
            
            end_time = time.time()
            logger.error(f"TaskManager _get_active_tasks time: {end_time - start_time}")
            return active_tasks
        
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return []
    
    def _get_expired_tasks(self) -> list[Task]:
        """Get all expired tasks."""
        return [task for task in self.active_tasks if task.timestamp < datetime.now() and not task.expired]
    
    def get_tasks_by_dates(self) -> list[dict]:
        """Group Tasks by date."""
        start_time = time.time()
        tasks_by_date = {}
        for task in self.active_tasks:
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

        end_time = time.time()
        logger.error(f"TaskManager get_tasks_by_dates time: {end_time - start_time}")
        return result 

    def _save_tasks_to_json(self, modified_task: Task = None) -> bool:
        """Save all tasks to the main tasks file."""
        start_time = time.time()
        try:
            task_data = [task.to_dict() for task in self.active_tasks]
            with open(self.tasks_file, "w") as f:
                json.dump(task_data, f, indent=2)
            
            # Only update first_task_file if the modified task affects it
            if modified_task and self.first_task:
                first_task_date = self.first_task[0].timestamp.date()
                modified_task_date = modified_task.timestamp.date()
                
                if modified_task_date == first_task_date:
                    self._update_first_task_file()
            
            end_time = time.time()
            logger.error(f"TaskManager _save_tasks_to_json time: {end_time - start_time}")

            return True
        
        except Exception as e:
            logger.error(f"Error saving tasks to file: {e}")
            return False
    
    def add_task(self, message: str, timestamp: datetime,
                 alarm_name: str, vibrate: bool) -> None:
        """Add a new Task to storage and tasks list."""
        start_time = time.time()
        task = Task(message=message, timestamp=timestamp,
                    alarm_name=alarm_name, vibrate=vibrate)
        
        # Add to in-memory list
        self.active_tasks.append(task)
        
        # Save to file
        if self._save_tasks_to_json(task):
            # Notify listeners
            self.dispatch("on_tasks_changed")
            # Schedule task_saved event to run after 0.1 seconds
            Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)
        
        end_time = time.time()
        logger.error(f"TaskManager add_task time: {end_time - start_time}")
    

    def edit_task(self, task_id: str) -> None:
        """
        Edit an existing task by ID.
        Copy Task data to NewTaskScreen and navigate to it.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        # Dispatch the on_task_edit event
        self.dispatch("on_task_edit", task=task)
        
        # Navigate to the edit screen
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
    def update_task(self, task_id: str, message: str,
                    timestamp: datetime, alarm_name: str, vibrate: bool) -> None:
        """Update an existing Task by its ID."""
        start_time = time.time()
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found for update")
            return
        
        # Update the task in memory
        task.timestamp = timestamp
        task.message = message
        task.alarm_name = alarm_name
        task.vibrate = vibrate
        
        # Save to file
        if self._save_tasks_to_json(task):
            logger.debug(f"Updated task: {task_id}")
            # Notify listeners
            self.dispatch("on_tasks_changed")
            # Schedule task_saved event to run after 0.1 seconds
            Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)
        
        end_time = time.time()
        logger.error(f"TaskManager update_task time: {end_time - start_time}")

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        start_time = time.time()
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        deleted_task = task
        self.active_tasks.remove(task)
        
        if self._save_tasks_to_json(deleted_task):
            logger.debug(f"Deleted task: {task_id}")
            # Notify listeners that tasks have changed
            self.dispatch("on_tasks_changed")
        
        end_time = time.time()
        logger.error(f"TaskManager delete_task time: {end_time - start_time}")

    def set_expired_tasks(self):
        """Set the expired tasks."""
        now = datetime.now()
        changed = False
        
        for task in self.active_tasks:
            if task.timestamp < now and not task.expired:
                task.expired = True
                changed = True
        
        if changed:
            self._save_tasks_to_json()
            
            self.dispatch("on_tasks_changed")

    def has_task_expired(self):
        """Check any of the tasks expired."""
        now = datetime.now()
        for task in self.active_tasks:
            if task.timestamp < now and not task.expired:
                return True
        return False
    
    def on_task_saved(self, task, *args):
        """Default handler for on_task_saved event"""
        logger.debug(f"on_task_saved event finished: {task}")
    
    def on_tasks_changed(self, *args):
        """Default handler for on_tasks_changed event"""
        logger.debug("on_tasks_changed event finished")
    
    def on_task_edit(self, task, *args):
        """Default handler for on_task_edit event"""
        logger.debug("on_task_edit event finished")

    def get_task_by_id(self, task_id: str) -> Task:
        """Get a task by its ID from memory."""
        return next((task for task in self.active_tasks if task.task_id == task_id), None)
    
    