import json

from datetime import datetime

from kivy.app import App

from src.managers.task_manager_utils import Task
from src.utils.logger import logger
from src.utils.platform import device_is_android, get_storage_path, validate_file

from src.settings import PATH, SCREEN


class TaskManager:
    """
    Manages Tasks and their storage.
    """
    def __init__(self):
        self.navigation_manager = App.get_running_app().navigation_manager
        self.new_task_screen = App.get_running_app().get_screen(SCREEN.NEW_TASK)
        
        self.task_file = get_storage_path(PATH.TASK_FILE)
        validate_file(self.task_file)
        
        self._load_saved_task_file()
        self.tasks = self.load_tasks()
    
    def _load_saved_task_file(self) -> bool:
        """Load the saved task_file on initial app load."""
        if not device_is_android():
            return True
        
        try:
            from jnius import autoclass  # type: ignore
            # Get asset manager
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            assets = activity.getAssets()
            
            try:
                with assets.open(PATH.TASK_FILE) as asset_file:
                    content = asset_file.read().decode("utf-8")
                
                with open(self.task_file, "w") as f:
                    f.write(content)                    
                return True
            
            except Exception as e:
                logger.error(f"Error loading task_file from Android assets: {e}")
                return False
        
        except Exception as e:
            logger.error(f"Error in Android setup: {e}")
            return False
    
    def load_tasks(self) -> list[Task]:
        """Load Tasks from task_file."""
        try:
            with open(self.task_file, "r") as f:
                task_data = json.load(f)
            
            tasks = [Task.from_dict(data) for data in task_data]
            # Sort tasks by timestamp
            tasks.sort(key=lambda task: task.timestamp)
            return tasks
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing task file: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return []
    
    def add_task(self, message: str, timestamp: datetime) -> None:
        """Add a new Task to self.tasks and save to task_file."""
        task = Task(message=message, timestamp=timestamp)
        self.tasks.append(task)
        self._save_tasks()
    
    def _save_tasks(self) -> None:
        """Save Tasks to task_file."""
        try:
            task_data = [task.to_dict() for task in self.tasks]
            with open(self.task_file, "w") as f:
                json.dump(task_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def edit_task(self, task_id: str) -> None:
        for task in self.tasks:
            if task.task_id == task_id:
                new_task_screen = App.get_running_app().get_screen(SCREEN.NEW_TASK)

                new_task_screen.in_edit_task_mode = True
                # Pre-fill the data
                new_task_screen.edit_mode = True
                new_task_screen.task_id_to_edit = task_id
                new_task_screen.task_input.set_text(task.message)
                new_task_screen.selected_date = task.timestamp.date()
                new_task_screen.selected_time = task.timestamp.time()
                new_task_screen.update_datetime_display()
                
                # Navigate to the edit screen
                self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
                return
        
        logger.error(f"Task with id {task_id} not found")

    def delete_task(self, task_id: str) -> None:
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                del self.tasks[i]
                self._save_tasks()
                
                # Refresh home screen
                home_screen = App.get_running_app().get_screen(SCREEN.HOME)
                home_screen.update_task_display()
                return
        
        logger.error(f"Task with id {task_id} not found")

    def get_tasks_by_dates(self) -> list[dict]:
        """Group Tasks by date."""
        tasks_by_date = {}
        for task in self.tasks:
            date_str = task.get_date_str()
            if date_str not in tasks_by_date:
                tasks_by_date[date_str] = []
            tasks_by_date[date_str].append(task)
        
        # Sort by timestamp (oldest first)
        sorted_dates = sorted(tasks_by_date.keys(), 
                             key=lambda date: next(iter(tasks_by_date[date])).timestamp,
                             reverse=False)
        
        result = []
        for date in sorted_dates:
            # Sort tasks within each date group by time (earliest first)
            sorted_tasks = sorted(tasks_by_date[date], key=lambda task: task.timestamp)
            result.append({
                "date": date,
                "tasks": sorted_tasks
            })
        
        return result 
