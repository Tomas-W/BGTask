import os

from datetime import datetime

from src.settings import PLATFORM, EXT, DIR


class AudioManagerUtils:
    """
    Utils for the AudioManager class that are unrelated to audio.
    """
    def __init__(self):
        pass

    def check_is_android(self):
        """Returns whether the app is running on Android."""
        from kivy.utils import platform
        return platform == PLATFORM.ANDROID
    
    def check_is_windows(self):
        """Returns whether the app is running on Windows."""
        import platform as py_platform
        return py_platform.system() == PLATFORM.WINDOWS
    
    def check_recording_permission(self):
        """Returns whether Android RECORD_AUDIO permission is granted."""
        if not self.is_android:
            return True
        
        try:
            from android.permissions import check_permission, Permission  # type: ignore
            return check_permission(Permission.RECORD_AUDIO)
            
        except ImportError:
            self.logger.error("Android permissions module not available. Ensure this is running on Android.")
            return False
        except AttributeError:
            self.logger.error("Permission.RECORD_AUDIO not found. Check Kivy's Android permissions module.")
            return False
        except RuntimeError as e:
            self.logger.error(f"Runtime error: {e}. Ensure request_permissions is called from the main thread.")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while requesting permissions: {e}")
            return False

    def request_android_recording_permissions(self):
        """Displays a dialog to request Android RECORD_AUDIO permissions."""
        if not self.is_android:
            return
            
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.RECORD_AUDIO],
                self.recording_permission_callback
            )
        except ImportError:
            self.logger.error("Android permissions module not available. Ensure this is running on Android.")
        except AttributeError:
            self.logger.error("Permission.RECORD_AUDIO not found. Check Kivy's Android permissions module.")
        except RuntimeError as e:
            self.logger.error(f"Runtime error: {e}. Ensure request_permissions is called from the main thread.")
        except Exception as e:
            self.logger.error(f"Unexpected error while requesting permissions: {e}")
    
    def recording_permission_callback(self, permissions, results):
        """Handles recording permission response."""
        if all(results):  # All permissions granted
            self.logger.debug(f"Permissions {permissions} granted")
            self.has_recording_permission = True
        else:
            self.logger.debug(f"Permissions {permissions} denied")
            self.has_recording_permission = False
    
    def _get_alarms_dir(self):
        """Get the directory path where the alarms are stored."""
        if self.is_android:
            try:
                from android.storage import app_storage_path  # type: ignore
                return os.path.join(app_storage_path(), DIR.ALARMS)
            
            except ImportError:
                self.logger.error("Android storage module not available.")
                return os.path.join(os.path.expanduser("~"), DIR.ALARMS)
        else:
            return os.path.join(DIR.ALARMS)
    
    def _get_recordings_dir(self):
        """Get the directory path where the recordings are stored."""
        if self.is_android:
            try:
                from android.storage import app_storage_path  # type: ignore
                return os.path.join(app_storage_path(), DIR.RECORDINGS)
            
            except ImportError:
                self.logger.error("Android storage module not available.")
                return os.path.join(os.path.expanduser("~"), DIR.RECORDINGS)
        else:
            return os.path.join(DIR.RECORDINGS)
    
    def validate_dir(self, dir_path):
        """Validate the alarm directory."""
        if not os.path.isdir(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                self.logger.debug(f"Created alarm directory: {dir_path}")

            except PermissionError:
                self.logger.error(f"Permission denied: Cannot create directory {dir_path}. Check app permissions.")
            except FileNotFoundError:
                self.logger.error(f"Invalid path: {dir_path} does not exist.")
            except OSError as e:
                self.logger.error(f"OS error while creating {dir_path}: {e}")
    
    def get_recording_path(self):
        """Get the path and filename of the just started recording."""
        filename = f"recording_{datetime.now().strftime('%H-%M-%S')}"
        path = os.path.join(self.recordings_dir, filename + EXT.WAV)
        return path, filename

    def alarm_name_to_path(self, name):
        """Convert an alarm name to a path."""
        return os.path.join(self.alarms_dir, f"{name}{EXT.WAV}")
    
    def alarm_path_to_name(self, path):
        """Convert a path to an alarm name."""
        return os.path.basename(path).split(".")[0]

    def set_alarm_name(self, name=None, path=None):
        """Set the name of the alarm"""
        if path:
            self.selected_alarm_name = self.alarm_path_to_name(path)
        elif name:
            self.selected_alarm_name = name
        else:
            self.logger.error("Either name or path must be provided")
            raise ValueError("Either name or path must be provided")
    
    def set_alarm_path(self, path=None, name=None):
        """Set the path of the alarm."""
        if path:
            self.selected_alarm_path = path
        elif name:
            self.selected_alarm_path = self.alarm_name_to_path(name)
        else:
            self.logger.error("Either path or name must be provided")
            raise ValueError("Either path or name must be provided")
    
    def recording_name_to_path(self, name):
        """Convert a recording name to a path."""
        return os.path.join(self.recordings_dir, f"{name}{EXT.WAV}")
    
    def recording_path_to_name(self, path):
        """Convert a path to a recording name."""
        return os.path.basename(path).split(".")[0]
    
    def set_recording_name(self, name=None, path=None):
        """Set the name of the recording."""
        if path:
            self.selected_recording_name = self.recording_path_to_name(path)
        elif name:
            self.selected_recording_name = name
        else:
            self.logger.error("Either name or path must be provided")
            raise ValueError("Either name or path must be provided")
    
    def set_recording_path(self, path=None, name=None):
        """Set the path of the recording."""
        if path:
            self.selected_recording_path = path
        elif name:
            self.selected_recording_path = self.recording_name_to_path(name)
        else:
            self.logger.error("Either path or name must be provided")
            raise ValueError("Either path or name must be provided")
