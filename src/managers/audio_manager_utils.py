import os
from datetime import datetime
from enum import Enum
from typing import Tuple

from src.utils.logger import logger
from src.settings import EXT


class AudioManagerUtils:
    """
    Utils for the AudioManager class.
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
        """Get the path and filename of a new recording."""
        filename = f"recording_{datetime.now().strftime('%H-%M-%S')}"
        path = os.path.join(self.recordings_dir, filename + EXT.WAV)
        return path, filename
    
    def get_audio_path(self, name: str) -> str:
        """
        Get the full path for an audio file based on its name and type.
        If type is not specified, it tries to find the file in both directories.
        """
        # Otherwise, check if file exists in either directory
        alarm_path = os.path.join(self.alarms_dir, f"{name}{EXT.WAV}")
        if os.path.exists(alarm_path):
            return alarm_path
            
        recording_path = os.path.join(self.recordings_dir, f"{name}{EXT.WAV}")
        if os.path.exists(recording_path):
            return recording_path
            
        # Default to recordings directory if file doesn't exist anywhere
        return recording_path
    
    def get_audio_name(self, path: str) -> str:
        """Extract the name from an audio file path"""
        return os.path.splitext(os.path.basename(path))[0]
    
    def select_audio(self, name: str = None, path: str = None) -> bool:
        """
        Select an audio file by name or path.
        Sets both selected_alarm_name and selected_alarm_path for compatibility.
        
        Returns True if successful, False otherwise.
        """
        if path:
            # Path provided - extract name
            if os.path.exists(path):
                self.selected_alarm_path = path
                self.selected_alarm_name = self.get_audio_name(path)
                return True
            else:
                logger.error(f"Audio file not found: {path}")
                return False
        
        elif name:
            # Name provided - find path
            path = self.get_audio_path(name)
            logger.error(f"Path: {path}")
            if os.path.exists(path):
                self.selected_alarm_path = path
                self.selected_alarm_name = name
                return True
            else:
                logger.error(f"Audio file not found for name: {name}")
                return False
        
        else:
            logger.error("Either name or path must be provided")
            return False
    
    def clear_selection(self) -> None:
        """Clear the selected audio"""
        self.selected_alarm_name = None
        self.selected_alarm_path = None
