from kivy.utils import platform

def start_background_service():
    """Start background service"""
    if platform != "android":
        return None
        
    try:
        from android import AndroidService  # type: ignore
        service = AndroidService("BGTask Background Service", "Task expiry monitoring service")
        service.start("BGTask service started")
        print("Started background service")
    
    except Exception as e:
        print(f"Error starting background service: {e}")
    return None


def notify_service_of_tasks_update():
    """Notify the service that Tasks have been updated"""
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

