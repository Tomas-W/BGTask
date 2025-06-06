import os
import time

from typing import Any

from managers.device.device_manager import DM


def is_service_running():
    """Check if the Service has written a heartbeat recently."""
    if not DM.is_android:
        return False
        
    try:
        # Check if heartbeat file exists
        if not os.path.exists(DM.PATH.SERVICE_HEARTBEAT_FLAG):
            return False
            
        # Read timestamp
        with open(DM.PATH.SERVICE_HEARTBEAT_FLAG, "r") as f:
            content = f.read().strip()
        # Handle empty file case
        if not content:
            return False
        
        # Check if heartbeat is recent
        timestamp = int(content)
        current_time = int(time.time())
        return (current_time - timestamp) <= DM.SETTINGS.HEARTBEAT_SEDCONDS
        
    except Exception as e:
        print(f"     Error checking service heartbeat: {str(e)}")
        return False


def start_background_service():
    """Start background service if not already running."""
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
