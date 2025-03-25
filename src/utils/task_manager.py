import os
import json
import shutil

from kivy.app import App
from kivy.utils import platform

from src.utils.task import Task
from src.settings import PATH, SCREEN


class TaskManager:
    """
    Manages tasks and their storage.
    """
    def __init__(self):
        self.navigation_manager = App.get_running_app().navigation_manager
        self.storage_path = self._get_storage_path()
        self.tasks = self.load_tasks()

        self.current_edit = {
            "task_id": None,
            "message": None,
            "timestamp": None
        }
        
    def _get_storage_path(self):
        """Get the storage path based on platform"""
        if platform == "android":
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), PATH.TASK_FILE)
        else:
            return os.path.join(PATH.TASK_FILE)
    
    def _copy_default_task_file(self):
        """Copy the default task file to the app's storage directory"""
        try:
            # Define source path for default task file
            if platform == "android":
                # On Android, check the app's assets directory
                from jnius import autoclass
                
                # Get the asset manager
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                activity = PythonActivity.mActivity
                assets = activity.getAssets()
                
                # Create directory for storage path if it doesn't exist
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                
                # Try to open and read the asset file
                try:
                    with assets.open(PATH.TASK_FILE) as asset_file:
                        content = asset_file.read().decode("utf-8")
                        
                    # Write to the storage location
                    with open(self.storage_path, "w") as f:
                        f.write(content)
                    
                    print(f"Copied default task file to {self.storage_path}")
                    return True
                except Exception as e:
                    print(f"Error reading asset file: {e}")
            else:
                # For desktop, check if a sample file exists in the assets directory
                default_task_path = os.path.join("assets", PATH.TASK_FILE)
                if os.path.exists(default_task_path):
                    os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                    shutil.copy(default_task_path, self.storage_path)
                    print(f"Copied default task file to {self.storage_path}")
                    return True
        except Exception as e:
            print(f"Error copying default task file: {e}")
        
        return False
    
    def add_task(self, message, timestamp):
        """Add a new task"""
        task = Task(message=message, timestamp=timestamp)
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def save_tasks(self):
        """Save tasks to storage"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            task_data = [task.to_dict() for task in self.tasks]
            with open(self.storage_path, "w") as f:
                json.dump(task_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False
    
    def load_tasks(self):
        """Load tasks from storage"""
        if not os.path.exists(self.storage_path):
            # Try to copy the default task file
            if self._copy_default_task_file():
                # If successful, try loading again
                if os.path.exists(self.storage_path):
                    try:
                        with open(self.storage_path, "r") as f:
                            task_data = json.load(f)
                        
                        tasks = [Task.from_dict(data) for data in task_data]
                        tasks.sort(key=lambda task: task.timestamp)
                        return tasks
                    except Exception as e:
                        print(f"Error loading copied tasks: {e}")
            
            # If copying failed or loading failed, return empty list
            return []
        
        try:
            with open(self.storage_path, "r") as f:
                task_data = json.load(f)
            
            self.tasks = [Task.from_dict(data) for data in task_data]
            # Sort tasks by timestamp
            self.tasks.sort(key=lambda task: task.timestamp)
            return self.tasks
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return []
    
    def edit_task(self, task_id):
        """Edit a task"""
        for task in self.tasks:
            if task.task_id == task_id:
                # Store the task data for editing
                self.current_edit["task_id"] = task_id
                self.current_edit["message"] = task.message
                self.current_edit["timestamp"] = task.timestamp
                
                # Navigate to the new task screen
                new_task_screen = App.get_running_app().root.get_screen(SCREEN.NEW_TASK)
                
                # Pre-fill the data
                new_task_screen.edit_mode = True
                new_task_screen.task_id_to_edit = task_id
                new_task_screen.task_input.text = task.message
                new_task_screen.selected_date = task.timestamp.date()
                new_task_screen.selected_time = task.timestamp.time()
                new_task_screen.update_datetime_display()
                
                # Navigate to the edit screen
                self.navigation_manager.go_to_new_task_screen(None)
                return True
                
        return False

    def delete_task(self, task_id):
        """Delete a task"""
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                del self.tasks[i]
                self.save_tasks()
                
                # Refresh home screen
                home_screen = App.get_running_app().root.get_screen(SCREEN.HOME)
                home_screen.update_task_display()
                return True
        return False
    
    def get_tasks_by_date(self):
        """Group tasks by date"""
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