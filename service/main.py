import json
import os
import time
from datetime import datetime

from kivy.logger import Logger

# Define constants
WAIT_TIME = 15  # seconds
FIRST_TASK_FILENAME = "app/src/assets/first_task.json"  # Just the relative path


def get_storage_path(path):
    """Returns the app-specific storage path for the given path."""
    app_dir = os.environ.get('ANDROID_PRIVATE', '')
    return os.path.join(app_dir, path)


def is_task_expired(task_data):
    """Check if a task's timestamp has passed the current time."""
    if not task_data:
        return False
    
    timestamp_str = task_data.get("timestamp", "")
    if not timestamp_str:
        return False
    
    try:
        task_time = datetime.fromisoformat(timestamp_str)
        return datetime.now() >= task_time
    except Exception as e:
        Logger.error(f"BGTaskService: Error parsing timestamp: {e}")
        return False


def check_task_file():
    """Check the first_task.json file to see if the task has expired."""
    try:
        # Get the path using the same method as the app
        first_task_path = get_storage_path(FIRST_TASK_FILENAME)
        Logger.info(f"BGTaskService: Looking for first_task.json at: {first_task_path}")
        
        # Check if file exists
        if not os.path.exists(first_task_path):
            Logger.warning(f"BGTaskService: First task file not found at {first_task_path}")
            return False
        
        # Load and parse the file
        with open(first_task_path, "r") as f:
            data = json.load(f)
        
        # Extract the first task from any date
        for date_key, tasks in data.items():
            if tasks and len(tasks) > 0:
                task = tasks[0]
                Logger.info(f"BGTaskService: Task expiry: {task.get('expired')}")
                Logger.info(f"BGTaskService: Task message: {task.get('message')}")
                
                # Check if the task is now expired
                if is_task_expired(task):
                    Logger.info("BGTaskService: Task has expired")
                    return True
                else:
                    Logger.info("BGTaskService: Task is not expired")
                    return False
        
        Logger.info("BGTaskService: No expired tasks found")
        return False
    
    except Exception as e:
        Logger.error(f"BGTaskService: Error checking task file: {e}")
        return False


if __name__ == "__main__":
    Logger.info("BGTaskService: Starting background service")
    
    # Run continuously checking for expired tasks
    while True:
        # Check if there's an expired task
        is_expired = check_task_file()
        
        if is_expired:
            Logger.info("BGTaskService: Found expired task")
        else:
            Logger.info("BGTaskService: No expired tasks found")
        
        # Wait before checking again
        Logger.info(f"BGTaskService: Waiting {WAIT_TIME} seconds before next check")
        time.sleep(WAIT_TIME) 