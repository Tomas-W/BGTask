import os
import time

from managers.device.device_manager import DM


def is_service_running():
    """Check if the service has written a heartbeat recently"""
    if not DM.is_android:
        return False
        
    try:
        # Check if heartbeat file exists
        if not os.path.exists(DM.PATH.SERVICE_HEARTBEAT_FLAG):
            return False
            
        # Read timestamp from file
        with open(DM.PATH.SERVICE_HEARTBEAT_FLAG, "r") as f:
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
        print(f"     Error checking service heartbeat: {str(e)}")
        return False


def start_background_service():
    """Start background service if not already running"""
    if not DM.is_android:
        return None
        
    try:
        # Only start if not already running
        if not is_service_running():
            from android import AndroidService  # type: ignore
            service = AndroidService("BGTask Background Service", "Task expiry monitoring service")
            service.start("BGTask service started")
            print("     Service not running - starting service")
        
        else:
            print("     Service already running")
    
    except Exception as e:
        print(f"     Error starting background service: {e}")
    return None


def _app_has_pending_intents() -> tuple[str, dict] | None:
    """
    Check for any pending intents when app starts.
    Returns a tuple of (action, extras) if a pending intent is found.
    Returns None if no pending intent is found.
    """
    try:
        from src.utils.logger import logger
        from jnius import autoclass  # type: ignore
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        if not hasattr(PythonActivity, "mActivity"):
            logger.debug("No activity available for checking pending intents")
            return None

        activity = PythonActivity.mActivity
        intent = activity.getIntent()
        if not intent:
            logger.debug("No intent found in activity")
            return None

        # Get all extras from intent
        extras = {}
        bundle = intent.getExtras()
        if bundle:
            for key in bundle.keySet():
                value = bundle.getString(key)
                if value:
                    extras[key] = value

        # Check if this is our pending intent by looking for our action in extras
        if "pending_action" in extras:
            logger.debug(f"Found our pending intent with action: {extras['pending_action']} and extras: {extras}")
            return extras["pending_action"], extras

        logger.debug("No pending intent found")
        return None

    except Exception as e:
        logger.error(f"Error checking pending intents: {e}", exc_info=True)
        return None


def _app_has_pending_intents_old() -> tuple[str, str] | None:
    """
    Check for any pending intents when app starts.
    Returns a tuple of (action, task_id) if a pending intent is found.
    Returns None if no pending intent is found.
    """
    from utils.logger import logger
    try:
        from jnius import autoclass  # type: ignore
        logger.error("Checking for pending intents")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        if not hasattr(PythonActivity, "mActivity"):
            logger.debug("No activity available for checking pending intents")
            return

        activity = PythonActivity.mActivity
        intent = activity.getIntent()
        if not intent:
            logger.debug("No intent found in activity")
            return

        # Get the action and task_id from the intent
        action = intent.getAction()
        if not action:
            logger.debug("No action found in intent")
            return

        # Extract pure action (remove package name)
        pure_action = action.split(".")[-1]
        task_id = intent.getStringExtra("task_id")
        logger.error(f"Found pending intent with action: {pure_action} and task_id: {task_id}")

        return pure_action, task_id

    except Exception as e:
        logger.error(f"Error checking pending intents: {e}", exc_info=True) 
