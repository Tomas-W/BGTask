import os

from datetime import datetime

from src.managers.audio.audio_manager_utils import AudioManagerUtils

from src.utils.logger import logger
from src.utils.platform import (device_is_android, device_is_windows, get_alarms_dir,
                                get_recordings_dir, validate_dir)

from src.settings import EXT

# Load AudioPlayer based on platform
from src.utils.platform import device_is_android, device_is_windows
if device_is_android():
    from src.managers.audio.android_audio import AndroidAudioPlayer
    is_android = True
elif device_is_windows():
    from src.managers.audio.windows_audio import WindowsAudioPlayer
    is_android = False
else:
    raise ImportError("No AudioPlayer could be loaded")


class AudioManager(AudioManagerUtils):
    """
    Manages playing and recording audio through the application.
    Has a platform-specific audio player.
    All audio players have the same interface.
    """
    def __init__(self):
        self.is_android: bool = is_android
        self.is_windows: bool = not is_android
        
        # Set audio player
        if self.is_android:
            self.audio_player = AndroidAudioPlayer()
            logger.debug("Using Android audio player")

        elif self.is_windows:
            self.audio_player = WindowsAudioPlayer()
            logger.debug("Using Windows audio player")

        else:
            logger.error("No audio player loaded")
            raise RuntimeError("Platform not supported")
        
        # Recordings
        self.recordings_dir: str = get_recordings_dir()
        validate_dir(self.recordings_dir)

        # Alarms
        self.alarms_dir: str = get_alarms_dir()
        validate_dir(self.alarms_dir)
        self.alarms: dict[str, str] = {}
        self.load_alarms()
        self.selected_alarm_name: str | None = None
        self.selected_alarm_path: str | None = None
        
        # States
        self.is_recording: bool = False
        self.has_recording_permission: bool = self.check_recording_permission()
    
    def load_alarms(self) -> None:
        """Load all audio files from alarms and recordings directories."""
        alarms = {}
        rec_count = 0
        alarm_count = 0

        # Load user recordings
        if os.path.exists(self.recordings_dir):
            for file in os.listdir(self.recordings_dir):
                if file.endswith(EXT.WAV):
                    name = os.path.splitext(file)[0]
                    alarms[name] = os.path.join(self.recordings_dir, file)
                    rec_count += 1

        # Load default alarms
        if os.path.exists(self.alarms_dir):
            for file in os.listdir(self.alarms_dir):
                if file.endswith(EXT.WAV):
                    name = os.path.splitext(file)[0]
                    alarms[name] = os.path.join(self.alarms_dir, file)
                    alarm_count += 1
        
        self.alarms = alarms
        logger.debug(f"Loaded {rec_count} recordings and {alarm_count} alarms")
    
    def start_recording_audio(self) -> bool:
        """
        Validates the audio player and permissions.
        Gets a new recording path and name, sets up a fresh recording session.
        Starts recording.
        Sets alarm name and path.
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return False
        
        # Check recording permissions
        if self.is_android and not self.has_recording_permission:
            self.request_android_recording_permissions()
            return False
        
        # Try setting up recording
        path, filename = self.create_recording_path()
        if not self.audio_player.setup_recording(path):
            return False
        
        # Try recording
        if not self.audio_player.start_recording():
            return False
        
        # Success
        self.is_recording = True
        self.selected_alarm_name = filename
        self.selected_alarm_path = path
        return True
    
    def stop_recording_audio(self) -> bool:
        """
        Stops the recording and saves the recording to the recordings directory.
        Has a small delay to ensure the file is fully written, checks if the file exists,
         and then adds the file to the recordings dictionary.
        """
        if not self.is_recording:
            logger.warning("No active recording to stop")
            return False
        
        recording_name = self.selected_alarm_name
        recording_path = self.selected_alarm_path        
        if not recording_path:
            logger.error("Recording path not set")
            self.is_recording = False
            return False
        
        # Stop the recording
        if not self.audio_player.stop_recording():
            self.is_recording = False
            return False

        # Verify recording
        if not self._verify_recording_file(recording_path):
            self.is_recording = False
            return False
            
        # Add alarm to AudioManager
        self.alarms[recording_name] = recording_path
        self.load_alarms()
        self.selected_alarm_name = recording_name
        self.selected_alarm_path = recording_path
        self.is_recording = False
        return True

    def start_playing_audio(self):
        """
        Validates the alarm path and plays the audio file.
        """
        path_to_play = self.selected_alarm_path
        
        if not path_to_play:
            logger.error("No alarm selected to play")
            return False
        
        if not os.path.exists(path_to_play):
            logger.error(f"Alarm file not found: {path_to_play}")
            return False
        
        if not self.audio_player:
            logger.error("No audio player available for this platform")
            return False
            
        try:
            # Try playing the audio
            return self.audio_player.play(path_to_play)
        
        except Exception as e:
            logger.error(f"Error playing alarm: {e}")
            return False

    def stop_playing_audio(self) -> bool:
        """
        Stops any currently playing audio.
        """
        # Try stopping the audio
        return self.audio_player.stop()

    def is_playing(self):
        """Check if an alarm is currently playing"""
        if not self.audio_player:
            return False

        return self.audio_player.is_playing()
    
    def select_alarm_audio(self, name: str) -> bool:
        """
        Searches for the file in the alarms and recordings directories.
        If found, sets selected_alarm_name and selected_alarm_path and returns True.
        Otherwise returns False.
        """
        # Alarm already in AudioManager
        if name in self.alarms:
            self.selected_alarm_path = self.alarms[name]
            self.selected_alarm_name = name
            return True
        
        else:
            path = self.get_audio_path(name)
            if path and os.path.exists(path):
                self.selected_alarm_path = path
                self.selected_alarm_name = name
                logger.debug(f"Selected alarm: {name} at {path}")
                return True
    
        logger.error(f"Alarm not found: {name} at {path}")
        return False
