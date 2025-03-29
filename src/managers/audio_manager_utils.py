import os

from datetime import datetime

from src.utils.logger import logger

from src.settings import EXT


class AudioManagerUtils:
    """
    Utils for the AudioManager class that are unrelated to audio.
    """
    def __init__(self):
        pass
    
    def check_recording_permission(self) -> bool:
        """Returns whether Android RECORD_AUDIO permission is granted."""
        if not self.is_android:
            return True
        
        try:
            from android.permissions import check_permission, Permission  # type: ignore
            return check_permission(Permission.RECORD_AUDIO)
        
        except ImportError:
            logger.error("Android permissions module not available. Ensure this is running on Android.")
            return False
        except AttributeError:
            logger.error("Permission.RECORD_AUDIO not found. Check Kivy's Android permissions module.")
            return False
        except RuntimeError as e:
            logger.error(f"Runtime error: {e}. Ensure request_permissions is called from the main thread.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
            return False
    
    def request_android_recording_permissions(self) -> None:
        """Displays a dialog to request Android RECORD_AUDIO permissions."""
        if not self.is_android:
            return
        
        logger.debug("Requesting recording permissions")
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.RECORD_AUDIO],
                self.recording_permission_callback
            )
        
        except ImportError:
            logger.error("Android permissions module not available. Ensure this is running on Android.")
        except AttributeError:
            logger.error("Permission.RECORD_AUDIO not found. Check Kivy's Android permissions module.")
        except RuntimeError as e:
            logger.error(f"Runtime error: {e}. Ensure request_permissions is called from the main thread.")
        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
    
    def recording_permission_callback(self, permissions: list[str], results: list[bool]) -> None:
        """Handles recording permission response."""
        if all(results):  # All permissions granted
            logger.debug(f"Permissions {permissions} granted")
            self.has_recording_permission = True
        else:
            logger.debug(f"Permissions {permissions} denied")
            self.has_recording_permission = False
    
    def get_recording_path(self) -> tuple[str, str]:
        """Get the path and filename of the just started recording."""
        filename = f"recording_{datetime.now().strftime('%H-%M-%S')}"
        path = os.path.join(self.recordings_dir, filename + EXT.WAV)
        return path, filename
    
    def alarm_name_to_path(self, name: str) -> str:
        """Convert an alarm name to a path."""
        return os.path.join(self.alarms_dir, f"{name}{EXT.WAV}")
    
    def alarm_path_to_name(self, path: str) -> str:
        """Convert a path to an alarm name."""
        return os.path.basename(path).split(".")[0]
    
    def set_alarm_name(self, name: str | None = None, path: str | None = None) -> None:
        """Set the name of the alarm"""
        if path:
            self.selected_alarm_name = self.alarm_path_to_name(path)
        elif name:
            self.selected_alarm_name = name
        else:
            logger.error("Either name or path must be provided")
            raise ValueError("Either name or path must be provided")
    
    def set_alarm_path(self, path: str | None = None, name: str | None = None) -> None:
        """Set the path of the alarm."""
        if path:
            self.selected_alarm_path = path
        elif name:
            self.selected_alarm_path = self.alarm_name_to_path(name)
        else:
            logger.error("Either path or name must be provided")
            raise ValueError("Either path or name must be provided")
    
    def recording_name_to_path(self, name: str) -> str:
        """Convert a recording name to a path."""
        return os.path.join(self.recordings_dir, f"{name}{EXT.WAV}")
    
    def recording_path_to_name(self, path: str) -> str:
        """Convert a path to a recording name."""
        return os.path.basename(path).split(".")[0]
    
    def set_recording_name(self, name: str | None = None, path: str | None = None) -> None:
        """Set the name of the recording."""
        if path:
            self.selected_recording_name = self.recording_path_to_name(path)
        elif name:
            self.selected_recording_name = name
        else:
            logger.error("Either name or path must be provided")
            raise ValueError("Either name or path must be provided")
    
    def set_recording_path(self, path: str | None = None, name: str | None = None) -> None:
        """Set the path of the recording."""
        if path:
            self.selected_recording_path = path
        elif name:
            self.selected_recording_path = self.recording_name_to_path(name)
        else:
            logger.error("Either path or name must be provided")
            raise ValueError("Either path or name must be provided")
