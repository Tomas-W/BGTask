import os
import time

from kivy.utils import platform

from service.service_utils import PATH


def is_service_running():
    """Check if the service has written a heartbeat recently"""
    if platform != "android":
        return False
        
    try:
        # Check if heartbeat file exists
        if not os.path.exists(PATH.SERVICE_HEARTBEAT_FLAG):
            return False
            
        # Read timestamp from file - store content first, then convert
        with open(PATH.SERVICE_HEARTBEAT_FLAG, "r") as f:
            content = f.read().strip()
            
        # Handle empty file case
        if not content:
            return False
            
        # Convert to integer after reading
        timestamp = int(content)
        
        # Check if heartbeat is recent (within last 60 seconds)
        current_time = int(time.time())
        return (current_time - timestamp) <= 120
        
    except Exception as e:
        print(f"Error checking service heartbeat: {str(e)}")
        return False


def start_background_service():
    """Start background service if not already running"""
    if platform != "android":
        return None
        
    try:
        # Only start if not already running
        from src.utils.logger import logger
        if not is_service_running():
            from android import AndroidService  # type: ignore
            service = AndroidService("BGTask Background Service", "Task expiry monitoring service")
            service.start("BGTask service started")
            logger.critical("Service not running - starting service")
        
        else:
            logger.critical("Service already running")
    
    except Exception as e:
        print(f"Error starting background service: {e}")
    return None


def notify_service_of_tasks_update():
    """Notify the service that Tasks have been updated by setting a flag file"""
    if platform != "android":
        return None
        
    try:
        from src.settings import PATH
        from src.utils.logger import logger
        with open(PATH.TASKS_CHANGED_FLAG, "w") as f:
            f.write("1")
        logger.debug("Created Tasks flag file for background service")
    
    except Exception as e:
        logger.error(f"Error creating Tasks flag file for background service: {e}")


def notify_service_of_task_notificaiton_removal():
    """Notify the service that a task notification has been removed by setting a flag file"""
    if platform != "android":
        return None 
        
    try:
        from src.settings import PATH
        from src.utils.logger import logger
        with open(PATH.TASK_NOTIFICATION_REMOVAL_FLAG, "w") as f:
            f.write("1")
        logger.debug("Created Task notification removal flag file for background service")
    
    except Exception as e:
        logger.error(f"Error creating Task notification removal flag file for background service: {e}")

