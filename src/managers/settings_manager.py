import time
import os

from src.managers.app_device_manager import DM

if DM.is_android:
    from jnius import autoclass  # type: ignore

from src.utils.logger import logger


class SettingsManager:
    """Manages app settings with simple, type-safe methods"""
    def __init__(self, max_retries=3, retry_delay=0.1):
        self.context = None
        self.prefs = None
        
        # Only try to initialize Android context if we're on Android
        if DM.is_android:
            self._init_context(max_retries, retry_delay)
            if not self.context:
                logger.error("Failed to initialize SettingsManager context after retries")
                raise RuntimeError("Could not initialize SettingsManager context")
            
            Context = autoclass("android.content.Context")
            self.prefs = self.context.getSharedPreferences("app_settings", Context.MODE_PRIVATE)
        else:
            # For non-Android platforms (like Windows), use a simple file-based settings
            self.settings_file = os.path.join(os.path.expanduser("~"), ".bgtask_settings.json")
            self.prefs = {}  # Will store settings in memory
            self._load_settings()

        self.cancelled_task_path = DM.get_storage_path("cancelled_task_id.txt")
        self.expired_task_path = DM.get_storage_path("expired_task_id.txt")
        # DM.validate_file(self.cancelled_task_path)
    
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
    
    def _load_settings(self):
        """Load settings from file for non-Android platforms"""
        try:
            if os.path.exists(self.settings_file):
                import json
                with open(self.settings_file, "r") as f:
                    self.prefs = json.load(f)
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.prefs = {}

    def _save_settings(self):
        """Save settings to file for non-Android platforms"""
        try:
            import json
            with open(self.settings_file, "w") as f:
                json.dump(self.prefs, f)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    # Modify the get/set methods to work on both platforms
    def set_string(self, key: str, value: str) -> None:
        if DM.is_android:
            self._get_editor().putString(key, value).commit()
        else:
            self.prefs[key] = value
            self._save_settings()
    
    def get_string(self, key: str, default: str = "") -> str:
        if DM.is_android:
            return self.prefs.getString(key, default)
        return self.prefs.get(key, default)
    
    def set_bool(self, key: str, value: bool) -> None:
        if DM.is_android:
            self._get_editor().putBoolean(key, value).apply()
        else:
            self.prefs[key] = value
            self._save_settings()
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        if DM.is_android:
            return self.prefs.getBoolean(key, default)
        return self.prefs.get(key, default)
    
    def set_int(self, key: str, value: int) -> None:
        if DM.is_android:
            self._get_editor().putInt(key, value).apply()
        else:
            self.prefs[key] = value
            self._save_settings()
    
    def get_int(self, key: str, default: int = 0) -> int:
        if DM.is_android:
            return self.prefs.getInt(key, default)
        return self.prefs.get(key, default)
