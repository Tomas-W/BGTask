import time

from kivy.utils import platform


def is_service_running() -> bool:
    """Check if our background service is already running"""
    start_time = time.time()
    if platform != "android":
        return False
        
    try:
        from jnius import autoclass  # type: ignore
        Integer = autoclass("java.lang.Integer")
        PythonService = autoclass("org.kivy.android.PythonService")
        Context = autoclass("android.content.Context")
        
        # Get the service context
        context = PythonService.mService
        if not context:
            return False
            
        # Get activity manager
        activity_manager = context.getSystemService(Context.ACTIVITY_SERVICE)
        if not activity_manager:
            return False
            
        # Get running services
        running_services = activity_manager.getRunningServices(Integer.MAX_VALUE)
        if not running_services:
            return False
            
        # Check if our service is in the list
        service_name = f"{context.getPackageName()}/org.kivy.android.PythonService"
        for service in running_services:
            if service.service.getClassName() == service_name:
                print(f"IS_SERVICE_RUNNING TIME: {time.time() - start_time:.4f}")
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking service status: {e}")
        return False

def start_background_service():
    """Start background service if not already running"""
    start_time = time.time()
    if platform != "android":
        return None
        
    try:
        # Only start if not already running
        if not is_service_running():
            from android import AndroidService  # type: ignore
            service = AndroidService("BGTask Background Service", "Task expiry monitoring service")
            service.start("BGTask service started")
            print(f"START_BACKGROUND_SERVICE TIME: {time.time() - start_time:.4f}")
        
        else:
            print("Background service already running")
    
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

