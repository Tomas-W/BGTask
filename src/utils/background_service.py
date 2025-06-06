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


def check_shared_preferences() -> tuple[str, dict] | None:
    """
    Checks for any pending actions in SharedPreferences.
    Returns a tuple of (action, extras) if a pending action is found.
    """
    try:
        from jnius import autoclass  # type: ignore

        # Get activity and context
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass('android.content.Context')
        
        if not hasattr(PythonActivity, "mActivity"):
            return None

        # Get SharedPreferences
        context = PythonActivity.mActivity.getApplicationContext()
        prefs = context.getSharedPreferences("pending_actions", Context.MODE_PRIVATE)
        
        # Get action
        action = prefs.getString("action", None)
        if not action:
            return None
            
        # Get all extras
        extras = {}
        all_keys = prefs.getAll().keySet()
        for key in all_keys:
            if key != "action":
                value = prefs.getString(key, None)
                if value:
                    extras[key] = value
                    
        # Clear the stored action
        editor = prefs.edit()
        editor.clear()
        editor.commit()
        
        print(f"Found pending action: {action} with extras: {extras}")
        return action, extras

    except Exception as e:
        print(f"Error checking pending actions: {e}")
        return None


def get_shared_preferences(pref_type: str, keys: list[str]) -> dict:
    """
    Reads specified keys from SharedPreferences.
    
    Args:
        pref_type: The SharedPreferences file to read from
        keys: List of keys to read
        
    Returns:
        Dictionary of found key-value pairs. Keys not found will be omitted.
    """
    try:
        from jnius import autoclass  # type: ignore

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass('android.content.Context')
        
        if not hasattr(PythonActivity, "mActivity"):
            return {}

        # Get SharedPreferences
        context = PythonActivity.mActivity.getApplicationContext()
        prefs = context.getSharedPreferences(pref_type, Context.MODE_PRIVATE)
        
        # Get requested values
        result = {}
        for key in keys:
            value = prefs.getString(key, None)
            if value is not None:
                result[key] = value
                
        # Clear the read values
        editor = prefs.edit()
        for key in keys:
            editor.remove(key)
        editor.commit()
        
        print(f"Read preferences from {pref_type}: {result}")
        return result

    except Exception as e:
        print(f"Error reading preferences: {e}")
        return {}


def get_and_delete_shared_preference(pref_type: str, key: str) -> str | None:
    """
    Reads and then deletes a single key from SharedPreferences.
    
    Args:
        pref_type: The SharedPreferences file to read from
        key: The specific key to read and delete
        
    Returns:
        The value if found, None if not found
    """
    try:
        from jnius import autoclass  # type: ignore

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass('android.content.Context')
        
        if not hasattr(PythonActivity, "mActivity"):
            return None

        # Get SharedPreferences
        context = PythonActivity.mActivity.getApplicationContext()
        prefs = context.getSharedPreferences(pref_type, Context.MODE_PRIVATE)
        
        # Get the value
        value = prefs.getString(key, None)
        
        # If value exists, delete just this key
        if value is not None:
            editor = prefs.edit()
            editor.remove(key)
            editor.commit()
            print(f"Read and deleted preference from {pref_type}: {key}={value}")
            
        return value

    except Exception as e:
        print(f"Error reading/deleting preference: {e}")
        return None
