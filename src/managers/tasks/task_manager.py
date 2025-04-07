import json
import time
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher

from src.managers.tasks.task_manager_utils import Task
from src.managers.tasks.task_db_manager import TaskDatabaseManager

from src.utils.logger import logger
from src.utils.platform import get_storage_path, validate_file, device_is_android

from src.settings import PATH, SCREEN


class TaskManager(EventDispatcher):
    """
    Manages Tasks and their storage.
    Uses SQLite on Android for better performance.
    """
    def __init__(self):
        super().__init__()
        self.navigation_manager = App.get_running_app().navigation_manager

        self.register_event_type("on_task_saved")
        self.register_event_type("on_tasks_changed")
        
        # Initialize SQLite database
        self.db_manager = TaskDatabaseManager()
        
        # For migration from JSON to SQLite
        self.task_file = get_storage_path(PATH.TASK_FILE)
        validate_file(self.task_file)
        
        # Only load today's tasks initially on Android for faster startup
        if device_is_android():
            self.tasks = self._load_today_tasks()
            # Check if we need to migrate from JSON
            self._migrate_from_json_if_needed()
            # Load remaining tasks in background
            Clock.schedule_once(self._load_remaining_tasks, 1)
        else:
            self.tasks = self.load_tasks()
            # Check if we need to migrate from JSON
            self._migrate_from_json_if_needed()

        # Editing
        self.selected_task_id: str | None = None
        # Date & Time
        self.selected_date: datetime | None = None
        self.selected_time: datetime | None = None
        # Vibration
        self.vibrate: bool = False
    
    def _update_json_task_file(self) -> None:
        """
        Updates the task_file.json with only today's or the nearest future tasks.
        This makes the StartScreen load faster as it only needs to read the minimal set of tasks.
        """
        try:
            today = datetime.now().date()
            all_tasks = sorted(self.tasks, key=lambda task: task.timestamp)
            
            # Find tasks from today or the nearest future date
            future_tasks = [task for task in all_tasks if task.timestamp.date() >= today]
            
            if not future_tasks:
                # No future tasks, so include the most recent past tasks
                task_data = [task.to_dict() for task in all_tasks[:5]] if all_tasks else []
            else:
                # Get tasks from the earliest future date
                earliest_date = future_tasks[0].timestamp.date()
                tasks_for_json = [task for task in future_tasks 
                                 if task.timestamp.date() == earliest_date]
                task_data = [task.to_dict() for task in tasks_for_json]
            
            # Write to JSON file
            with open(self.task_file, "w") as f:
                json.dump(task_data, f, indent=2)
            
            logger.debug(f"Updated task_file.json with {len(task_data)} tasks for StartScreen")
        
        except Exception as e:
            logger.error(f"Error updating task_file.json: {e}")
    
    def _migrate_from_json_if_needed(self):
        """Check if we need to migrate tasks from JSON to SQLite."""
        try:
            # If we already have tasks in SQLite, skip migration
            if self.tasks:
                return
                
            # Load tasks from JSON
            with open(self.task_file, "r") as f:
                task_data = json.load(f)
            
            if not task_data:
                return
                
            # Convert to Task objects
            json_tasks = [Task.from_dict(data) for data in task_data]
            
            # Prepare data for bulk insert
            bulk_data = [
                {
                    "task_id": task.task_id,
                    "message": task.message,
                    "timestamp": task.timestamp.isoformat(),
                    "alarm_name": task.alarm_name,
                    "vibrate": 1 if task.vibrate else 0,
                    "expired": 1 if task.expired else 0
                }
                for task in json_tasks
            ]
            
            # Save tasks to SQLite database in bulk
            success = self.db_manager.save_tasks_in_bulk(bulk_data)
            
            if success:
                # Update our tasks list
                self.tasks = json_tasks if not self.tasks else self.tasks + json_tasks
                # Sort by timestamp
                self.tasks.sort(key=lambda task: task.timestamp)
                # Notify listeners
                self.dispatch("on_tasks_changed")
                logger.info(f"Successfully migrated {len(json_tasks)} tasks from JSON to SQLite")
            
        except Exception as e:
            logger.error(f"Error migrating from JSON: {e}")
    
    def _load_today_tasks(self):
        """Load only today's tasks for faster initial loading."""
        try:
            task_data = self.db_manager.get_today_tasks()
            tasks = [self._create_task_from_db(data) for data in task_data]
            return tasks
        except Exception as e:
            logger.error(f"Error loading today's tasks: {e}")
            return []
    
    def _load_remaining_tasks(self, dt):
        """Load all tasks and merge with already loaded today's tasks."""
        try:
            # Get all task IDs that are already loaded
            today_task_ids = {task.task_id for task in self.tasks}
            
            # Get all tasks from database
            all_task_data = self.db_manager.get_all_tasks()
            
            # Filter out tasks that are already loaded
            new_tasks = [
                self._create_task_from_db(data)
                for data in all_task_data
                if data["task_id"] not in today_task_ids
            ]
            
            # Add new tasks to our list
            self.tasks.extend(new_tasks)
            
            # Sort tasks by timestamp
            self.tasks.sort(key=lambda task: task.timestamp)
            
            # Update the JSON file for StartScreen
            self._update_json_task_file()
            
            # Notify listeners if any tasks were added
            if new_tasks:
                self.dispatch("on_tasks_changed")
                
            logger.debug(f"Loaded {len(new_tasks)} additional tasks in background")
        except Exception as e:
            logger.error(f"Error loading remaining tasks: {e}")
    
    def set_expired_tasks(self):
        """Set the expired tasks."""
        changed_count = self.db_manager.mark_expired_tasks()
        
        if changed_count > 0:
            # Update our local task objects
            now = datetime.now()
            for task in self.tasks:
                if task.timestamp < now and not task.expired:
                    task.expired = True
            
            # Update the JSON file for StartScreen
            self._update_json_task_file()
            
            # Notify listeners
            self.dispatch("on_tasks_changed")
    def has_task_expired(self):
        """Check any of the tasks expired."""
        now = datetime.now()
        for task in self.tasks:
            if task.timestamp < now and not task.expired:
                return True
        return False
    
    def on_task_saved(self, task, *args):
        """Default handler for on_task_saved event"""
        logger.debug(f"on_task_saved event finished: {task}")
    
    def on_tasks_changed(self, *args):
        """Default handler for on_tasks_changed event"""
        logger.debug("on_tasks_changed event finished")
    
    def _create_task_from_db(self, data):
        """Create a Task object from database row."""
        return Task(
            task_id=data["task_id"],
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            alarm_name=data["alarm_name"],
            vibrate=bool(data["vibrate"]),
            expired=bool(data["expired"])
        )
    
    def load_tasks(self) -> list[Task]:
        """Load all Tasks from database."""
        try:
            task_data = self.db_manager.get_all_tasks()
            
            tasks = [self._create_task_from_db(data) for data in task_data]
            # Sort tasks by timestamp
            tasks.sort(key=lambda task: task.timestamp)
            
            return tasks
        
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return []
    
    def get_task_by_id(self, task_id: str) -> Task:
        """
        Get a task by its ID from memory first, then from database.
        Caches result for faster access.
        """
        # Try to find in memory first (much faster)
        task = next((task for task in self.tasks if task.task_id == task_id), None)
        
        # If not found in memory, try database
        if not task and device_is_android():
            data = self.db_manager.get_task_by_id(task_id)
            if data:
                task = self._create_task_from_db(data)
                # Add to in-memory cache
                self.tasks.append(task)
        
        return task
    
    def add_task(self, message: str, timestamp: datetime,
                 alarm_name: str, vibrate: bool) -> None:
        """Add a new Task to database and tasks list."""
        task = Task(message=message, timestamp=timestamp,
                    alarm_name=alarm_name, vibrate=vibrate)
        
        # Add to database
        success = self.db_manager.add_task(
            task.task_id,
            task.message,
            task.timestamp.isoformat(),
            task.alarm_name,
            task.vibrate,
            task.expired
        )
        
        if success:
            # Add to in-memory list
            self.tasks.append(task)
            
            # Update the JSON file for StartScreen
            self._update_json_task_file()
            
            # Notify listeners
            self.dispatch("on_tasks_changed")
            # Schedule task_saved event to run after 0.1 seconds
            Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)
    
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
                    timestamp: datetime, alarm_name: str, vibrate: bool) -> None:
        """Update an existing Task by its ID."""
        task = next((task for task in self.tasks if task.task_id == task_id), None)
        if not task:
            logger.error(f"Task with id {task_id} not found for update")
            return
        
        # Update the task in memory
        task.timestamp = timestamp
        task.message = message
        task.alarm_name = alarm_name
        task.vibrate = vibrate
        
        # Update in database
        success = self.db_manager.update_task(
            task_id,
            message,
            timestamp.isoformat(),
            alarm_name,
            vibrate,
            task.expired
        )
        
        if success:
            logger.debug(f"Updated task: {task_id}")
            
            # Update the JSON file for StartScreen
            self._update_json_task_file()
            
            # Notify listeners
            self.dispatch("on_tasks_changed")
            # Schedule task_saved event to run after 0.1 seconds
            Clock.schedule_once(lambda dt: self.dispatch("on_task_saved", task=task), 0.1)

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        task = next((task for task in self.tasks if task.task_id == task_id), None)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        # Delete from database
        success = self.db_manager.delete_task(task_id)
        
        if success:
            # Remove from in-memory list
            self.tasks.remove(task)
            logger.debug(f"Deleted task: {task_id}")
            
            # Update the JSON file for StartScreen
            self._update_json_task_file()
            
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
