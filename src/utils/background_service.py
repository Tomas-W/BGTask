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
