import time
import os

from datetime import datetime

try:
    from jnius import autoclass  # type: ignore
except ImportError:
    pass

from src.managers.device_manager import DM

from src.utils.logger import logger


class SettingsManager:
    """Manages app settings with simple, type-safe methods"""
    def __init__(self, max_retries=3, retry_delay=0.1):
        self.context = None
        self.prefs = None
        self._init_context(max_retries, retry_delay)

        self.cancelled_task_path = DM.get_storage_path("cancelled_task_id.txt")
        # DM.validate_file(self.cancelled_task_path)
        
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
        """Set a string value with synchronous commit"""
        self._get_editor().putString(key, value).commit()  # Use commit() instead of apply()
    
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

    def set_cancelled_task_id(self, task_id: str) -> None:
        """Store the ID of a task that was cancelled via notification swipe/cancel button"""
        logger.critical(f"Setting cancelled task ID: {task_id}")
        try:
            with open(self.cancelled_task_path, "w") as f:
                f.write(task_id)
            logger.critical(f"Wrote cancelled task ID to file: {task_id}")
        
        except Exception as e:
            logger.error(f"Error writing cancelled task ID to file: {e}")

    def get_cancelled_task_id(self) -> str:
        """Get the ID of a task that was cancelled via notification swipe/cancel button"""
        try:
            if os.path.exists(self.cancelled_task_path):
                with open(self.cancelled_task_path, "r") as f:
                    task_id = f.read().strip()
                logger.critical(f"Read cancelled task ID from file: {task_id}")
                return task_id
        
        except Exception as e:
            logger.error(f"Error reading cancelled task ID from file: {e}")
        return ""

    def clear_cancelled_task_id(self, *args, **kwargs) -> None:
        """Clear the cancelled task ID after handling"""
        try:
            if os.path.exists(self.cancelled_task_path):
                os.remove(self.cancelled_task_path)
                logger.critical("Removed cancelled task ID file")
        
        except Exception as e:
            logger.error(f"Error removing cancelled task ID file: {e}")
