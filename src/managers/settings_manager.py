import time

from datetime import datetime

try:
    from jnius import autoclass  # type: ignore
except ImportError:
    pass


class SettingsManager:
    """Manages app settings with simple, type-safe methods"""
    def __init__(self, max_retries=3, retry_delay=0.1):
        self.context = None
        self.prefs = None
        self._init_context(max_retries, retry_delay)
        
        if not self.context:
            from src.utils.logger import logger
            logger.error("Failed to initialize SettingsManager context after retries")
            raise RuntimeError("Could not initialize SettingsManager context")
        
        Context = autoclass("android.content.Context")
        self.prefs = self.context.getSharedPreferences("app_settings", Context.MODE_PRIVATE)
    
    def _init_context(self, max_retries: int, retry_delay: float) -> None:
        """Initialize context with retries for service"""
        for attempt in range(max_retries):
            try:
                # Try to get context from PythonActivity (main app)
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                self.context = PythonActivity.mActivity
                if self.context:
                    return
            except:
                pass

            try:
                # Try to get context from PythonService (background service)
                PythonService = autoclass("org.kivy.android.PythonService")
                self.context = PythonService.mService
                if self.context:
                    return
            except:
                pass

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    def _get_editor(self):
        """Get a fresh editor instance"""
        return self.prefs.edit()
    
    # Simple, type-specific methods that are easy to use and extend
    def set_string(self, key: str, value: str) -> None:
        self._get_editor().putString(key, value).apply()
    
    def get_string(self, key: str, default: str = "") -> str:
        return self.prefs.getString(key, default)
    
    def set_bool(self, key: str, value: bool) -> None:
        self._get_editor().putBoolean(key, value).apply()
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        return self.prefs.getBoolean(key, default)
    
    def set_int(self, key: str, value: int) -> None:
        self._get_editor().putInt(key, value).apply()
    
    def get_int(self, key: str, default: int = 0) -> int:
        return self.prefs.getInt(key, default)
    
    # Your specific methods using the above
    def save_last_open_time(self) -> None:
        """Save the current timestamp as the last time the app was open"""
        current_time = str(int(datetime.now().timestamp() * 1000))  # milliseconds as string
        self.set_string("last_open_time", current_time)

    def get_last_open_time(self) -> int:
        """Get the timestamp of when the app was last open in milliseconds"""
        try:
            return int(self.get_string("last_open_time", "0"))  # Convert string back to int
        except ValueError:
            return 0  # Default to 0 if conversion fails

    def did_task_expire_after_last_open(self, task_timestamp: datetime) -> bool:
        """Check if a task expired after the last time the app was open"""
        try:
            last_open = int(self.get_string("last_open_time", "0")) / 1000  # Convert to seconds
            task_time = task_timestamp.timestamp()
            return task_time > last_open
        except ValueError:
            return False  # If we can't parse the timestamp, assume task didn't expire
    
    def set_cancelled_task_id(self, task_id: str) -> None:
        """Store the ID of a task that was cancelled via notification swipe"""
        self.set_string("cancelled_task_id", task_id)
    
    def get_cancelled_task_id(self) -> str:
        """Get the ID of a task that was cancelled via notification swipe"""
        return self.get_string("cancelled_task_id", "")
    
    def clear_cancelled_task_id(self) -> None:
        """Clear the cancelled task ID after handling it"""
        self.set_string("cancelled_task_id", "")
