import os
import time

from datetime import datetime

from src.utils.logger import logger

from src.settings import EXT


class AudioManagerUtils:
    """
    Utilities for the AudioManager class.
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
        
        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
            return False
    
    def request_android_recording_permissions(self) -> None:
        """Displays a dialog to request Android RECORD_AUDIO permissions."""
        if not self.is_android:
            return
        
        logger.debug("Requesting Android recording permissions")
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.RECORD_AUDIO],
                self.recording_permission_callback
            )

        except Exception as e:
            logger.error(f"Unexpected error while requesting permissions: {e}")
    
    def recording_permission_callback(self, permissions: list[str], results: list[bool]) -> None:
        """
        Sets has_recording_permission based on the results of the permission request.
        """
        if all(results):
            logger.debug(f"Permissions {permissions} granted")
            self.has_recording_permission = True
        else:
            logger.debug(f"Permissions {permissions} denied")
            self.has_recording_permission = False
    
    def create_recording_path(self) -> tuple[str, str]:
        """
        Get the path and filename of a new recording.
        Format: ../{recordings_dir}/recording_HH-MM-SS.wav
        """
        filename = f"recording_{datetime.now().strftime('%H-%M-%S')}"
        path = os.path.join(self.recordings_dir, filename + EXT.WAV)
        return path, filename
    
    def get_audio_path(self, name: str) -> str | None:
        """
        Searches for the file in the alarms and recordings directories.
        Returns the path if found, otherwise returns None.
        """
        # Alarm already in AudioManager
        if name in self.alarms:
            return self.alarms[name]
            
        # Check default alarms
        alarm_path = os.path.join(self.alarms_dir, f"{name}{EXT.WAV}")
        if os.path.exists(alarm_path):
            return alarm_path
        
        # Check user recordings
        recording_path = os.path.join(self.recordings_dir, f"{name}{EXT.WAV}")
        if os.path.exists(recording_path):
            return recording_path
            
        logger.error(f"Audio file not found for name: {name}")
        return None
    
    def _verify_recording_file(self, path: str, max_attempts: int = 3) -> bool:
        """Verify recording file exists and adds a small delay for Windows."""
        for attempt in range(max_attempts):
            try:
                # Windows delay
                if self.is_windows and attempt > 0:
                    time.sleep(0.1)
                
                # Verify contents
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        if f.read(1024):
                            return True
            
            except Exception as e:
                logger.warning(f"File verification attempt {attempt+1} failed: {e}")
        
        logger.error(f"Failed to verify recording file: {path}")
        return False
