import os

from typing import TYPE_CHECKING

from managers.audio.audio_manager import AudioManager
from managers.tasks.task import Task
from managers.device.device_manager import DM
from src.app_managers.permission_manager import PM

from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp


class AppAudioManager(AudioManager):
    """
    Manages playing and recording audio in the application.
    Extends on AudioManager to add app-specific functionality.
    """
    def __init__(self, app: "TaskApp"):
        super().__init__()
        self.app = app
        
        # SelectAlarmScreen
        self.alarms: dict[str, str] = {}
        self.load_alarms()  # Loads alarms and recordings into self.alarms
        self.selected_alarm_name: str | None = None
        self.selected_alarm_path: str | None = None
        self.selected_vibrate: bool = False
        self.selected_keep_alarming: bool = False
        # Triggering alarm
        self.alarm_is_triggered: bool = False
        self.current_alarm_path: str | None = None
        self.task: Task | None
        
        # Recording
        self.is_recording: bool = False
        
    def load_alarms(self) -> None:
        """
        Loads all audio files from alarms and recordings directories.
        Sorts the files by name and saves them to self.alarms.
        """
        alarms = {}
        # Load user recordings
        user_recordings = self._load_alarms(DM.DIR.RECORDINGS)
        alarms.update(user_recordings)
        # Load default alarms
        default_alarms = self._load_alarms(DM.DIR.ALARMS)
        alarms.update(default_alarms)
        # Sort and save
        sorted_alarms = sorted(alarms.items(), key=lambda x: x[0])
        self.alarms = dict(sorted_alarms)
        
    def _load_alarms(self, directory: str) -> dict[str, str]:
        """
        Returns a dictionary of audio files from a directory.
        """
        alarms = {}
        try:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.endswith(DM.EXT.WAV):
                        name = os.path.splitext(file)[0]
                        alarms[name] = os.path.join(directory, file)
        
        except Exception as e:
            logger.error(f"Error loading alarms: {e}")
        
        return alarms
    
    def start_recording_audio(self) -> bool:
        """
        Validates the audio player and permissions.
        Gets a new recording path and name, sets up a fresh recording session.
        Starts recording.
        Sets alarm name and path.
        """
        if self.is_recording:
            logger.warning("Recording already in progress, cancelling and starting new recording")
            self.stop_recording_audio()
                
        # Check recording permissions, ask if needed
        if not PM.validate_permission(PM.RECORD_AUDIO):
            return False
        
        # Try setting up recording
        path, filename = self.get_recording_path()
        if not self.audio_recorder.setup_recording(path):
            return False
        
        # Try recording
        if not self.audio_recorder.start_recording():
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
            logger.error("Error stopping recording, recording path not set")
            self.is_recording = False
            return False
        
        # Stop the recording
        if not self.audio_recorder.stop_recording():
            self.is_recording = False
            logger.error("Error stopping recording, failed to stop recording")
            return False

        # Verify recording
        if not DM.validate_file(recording_path):
            self.is_recording = False
            logger.error(f"Error stopping recording, recording file not found: {recording_path}")
            return False
            
        self.load_alarms()
        self.selected_alarm_name = recording_name
        self.selected_alarm_path = recording_path
        self.is_recording = False
        return True

    def start_playing_audio(self, audio_path: str) -> bool:
        """
        Validates the alarm path and plays the audio file.
        """
        if not DM.validate_file(audio_path):
            logger.error(f"Error playing audio, file not found: {audio_path}")
            return False
        
        if not self.audio_player:
            logger.error("Error playing audio, no audio player available")
            return False
            
        try:
            return self.audio_player.play(audio_path)
        
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def stop_playing_audio(self) -> bool:
        """
        Stops any currently playing audio.
        """
        return self.audio_player.stop()
    
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
                self.alarms[name] = path
                return True
    
        logger.error(f"Error selecting alarm, alarm not found: {name} at {path}")
        return False
    
    def update_alarm_name(self, new_name: str) -> bool:
        """
        Renames the selected alarm file and updates self.alarms.
        """
        if not self.selected_alarm_path:
            logger.error("Error updating alarm name, no alarm selected to rename")
            return False
        
        # Rename file
        directory = os.path.dirname(self.selected_alarm_path)
        new_path = os.path.join(directory, f"{new_name}{DM.EXT.WAV}")
        os.rename(self.selected_alarm_path, new_path)
        
        # Renew memory
        old_name = self.selected_alarm_name
        del self.alarms[old_name]
        self.alarms[new_name] = new_path
        self.selected_alarm_name = new_name
        self.selected_alarm_path = new_path
        
        # Update UI
        self.app.get_screen(DM.SCREEN.SELECT_ALARM).update_selected_alarm_text()
        return True
    
    def delete_alarm(self, name: str) -> bool:
        """
        Deletes the alarm file and removes it from memory.
        """
        path = self.get_audio_path(name)
        if not path:
            logger.error(f"Error deleting alarm, alarm file not found: {name}")
            return False
        
        try:
            os.remove(path)
            logger.trace(f"Deleted alarm: {name} at {path}")
            self.selected_alarm_name = None
            self.selected_alarm_path = None
            self.load_alarms()
            
            self.app.get_screen(DM.SCREEN.SELECT_ALARM).update_screen_state()
            return True
        
        except Exception as e:
            logger.error(f"Error deleting alarm: {e}")
            return False
