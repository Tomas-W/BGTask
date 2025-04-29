import json
import os
import time
from datetime import datetime

# Define constants
WAIT_TIME = 15  # seconds
SERVICE_FLAG_FILE = "app/src/assets/service_stop.flag"
SERVICE_TASK_FILE = "app/src/assets/first_task.json"


def get_storage_path(path):
    """Returns the app-specific storage path for the given path."""
    app_dir = os.environ.get("ANDROID_PRIVATE", "")
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
        print(f"BGTaskService: Error parsing timestamp: {e}")
        return False


def check_task_file():
    """Check the first_task.json file to see if the task has expired."""
    try:
        # Get the path using the same method as the app
        first_task_path = get_storage_path(SERVICE_TASK_FILE)
        print(f"BGTaskService: Looking for first_task.json at: {first_task_path}")
        
        # Check if file exists
        if not os.path.exists(first_task_path):
            print(f"BGTaskService: First task file not found at {first_task_path}")
            return False
        
        # Load and parse the file
        with open(first_task_path, "r") as f:
            data = json.load(f)
        
        # Extract the first task from any date
        for date_key, tasks in data.items():
            if tasks and len(tasks) > 0:
                task = tasks[0]
                print(f"BGTaskService: Task expiry: {task.get('expired')}")
                print(f"BGTaskService: Task message: {task.get('message')}")
                
                # Check if the task is now expired
                if is_task_expired(task):
                    print("BGTaskService: Task has expired")
                    return True
                else:
                    print("BGTaskService: Task is not expired")
                    return False
        
        print("BGTaskService: No expired tasks found")
        return False
    
    except Exception as e:
        print(f"BGTaskService: Error checking task file: {e}")
        return False


def should_stop_service():
    """Check if the service should stop based on the stop flag file."""
    stop_flag_path = get_storage_path(SERVICE_FLAG_FILE)
    return os.path.exists(stop_flag_path)


def remove_stop_flag():
    """Remove the stop flag file if it exists."""
    stop_flag_path = get_storage_path(SERVICE_FLAG_FILE)
    if os.path.exists(stop_flag_path):
        try:
            os.remove(stop_flag_path)
        except Exception as e:
            print(f"BGTaskService: Error removing stop flag: {e}")


if __name__ == "__main__":
    print("BGTaskService: Starting background service")
    
    # Remove any existing stop flag when service starts
    remove_stop_flag()
    
    # Run continuously checking for expired tasks
    while True:
        # Check if service should stop
        if should_stop_service():
            print("BGTaskService: Stop flag detected, stopping service")
            break
            
        # Check if there's an expired task
        is_expired = check_task_file()
        
        if is_expired:
            print("BGTaskService: Found expired task")
        else:
            print("BGTaskService: No expired tasks found")
        
        # Wait before checking again
        print(f"BGTaskService: Waiting {WAIT_TIME} seconds before next check")
        time.sleep(WAIT_TIME) 