import os
import time

from datetime import datetime

from src.managers.device.device_manager import DM

from src.utils.logger import logger

from src.settings import EXT, DATE


class AudioManagerUtils:
    """
    Utilities for the AudioManager class.
    """
    def __init__(self):
        pass
    
    def create_recording_path(self) -> tuple[str, str]:
        """
        Get the path and filename of a new recording.
        Format: ../{recordings_dir}/recording_HH_MM_SS.wav
        """
        name = "recording_"
        timestamp = datetime.now().strftime(DATE.RECORDING)
        while True:
            path = os.path.join(self.recordings_dir, name + timestamp + EXT.WAV)
            if os.path.exists(path):
                logger.warning(f"Recording file already exists: {path}")
                name += "_"
            else:
                break

        filename = f"{name}{timestamp}"
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
