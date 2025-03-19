import os
import json

from src.utils.task import Task

from src.settings import PATH


class TaskManager:
    """
    Manages tasks and their storage.
    """
    def __init__(self):
        self.storage_path = self._get_storage_path()
        self.tasks = self.load_tasks()
        
    def _get_storage_path(self):
        """Get the storage path based on platform"""
        from kivy.utils import platform
        
        if platform == "android":
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), "tasks.json")
        else:
            return os.path.join(PATH.SRC, "tasks.json")
    
    def add_task(self, message, timestamp):
        """Add a new task"""
        task = Task(message=message, timestamp=timestamp)
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def save_tasks(self):
        """Save tasks to storage"""
        try:
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