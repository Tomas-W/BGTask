import os

from kivy.app import App

from managers.audio.audio_manager import AudioManager
from managers.tasks.task import Task

from managers.device.device_manager import DM
from src.managers.permission_manager import PM

from src.utils.logger import logger


class AppAudioManager(AudioManager):
    """
    Manages playing and recording audio in the application.
    Extends on AudioManager to add app-specific functionality.
    """
    def __init__(self):
        super().__init__()
        
        # Bind events
        app = App.get_running_app()
        app.task_manager.expiry_manager.bind(on_task_expired_trigger_alarm=self.trigger_alarm)
        app.task_manager.expiry_manager.bind(on_task_cancelled_stop_alarm=self.stop_alarm)
        app.task_manager.expiry_manager.bind(on_task_snoozed_stop_alarm=self.stop_alarm)
        app.bind(on_resume=self.stop_alarm)

        # SelectAlarmScreen
        self.alarms: dict[str, str] = {}
        self.load_alarms()  # Loads alarms and recordings into self.alarms
        self.selected_alarm_name: str | None = None
        self.selected_alarm_path: str | None = None
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
        nr_recordings = len(user_recordings)
        alarms.update(user_recordings)

        # Load default alarms
        default_alarms = self._load_alarms(DM.DIR.ALARMS)
        nr_alarms = len(default_alarms)
        alarms.update(default_alarms)

        # Sort and save
        sorted_alarms = sorted(alarms.items(), key=lambda x: x[0])
        self.alarms = dict(sorted_alarms)
        logger.trace(f"Loaded {nr_recordings} recordings and {nr_alarms} alarms")
    
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
            logger.warning("Recording already in progress")
            return False
        
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
            logger.error("Recording path not set")
            self.is_recording = False
            return False
        
        # Stop the recording
        if not self.audio_recorder.stop_recording():
            self.is_recording = False
            logger.error("Failed to stop recording")
            return False

        # Verify recording
        if not DM.validate_file(recording_path):
            self.is_recording = False
            logger.error(f"Recording file not found: {recording_path}")
            return False
            
        # self.alarms[recording_name] = recording_path
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
            logger.error(f"Alarm file not found: {audio_path}")
            return False
        
        if not self.audio_player:
            logger.error("No audio player available")
            return False
            
        try:
            return self.audio_player.play(audio_path)
        
        except Exception as e:
            logger.error(f"Error playing alarm: {e}")
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
    
        logger.error(f"Alarm not found: {name} at {path}")
        return False
    
    def update_alarm_name(self, new_name: str) -> bool:
        """
        Renames the selected alarm file and updates self.alarms.
        """
        if not self.selected_alarm_path:
            logger.error("No alarm selected to rename")
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
        from kivy.app import App
        from src.settings import SCREEN
        select_alarm_screen = App.get_running_app().get_screen(SCREEN.SELECT_ALARM)
        select_alarm_screen.update_selected_alarm_text()
        return True
    
    def delete_alarm(self, name: str) -> bool:
        """
        Deletes the alarm file and removes it from memory.
        """
        path = self.get_audio_path(name)
        if not path:
            logger.error(f"Alarm file not found: {name}")
            return False
        
        try:
            os.remove(path)
            logger.trace(f"Deleted alarm: {name} at {path}")
            self.selected_alarm_name = None
            self.selected_alarm_path = None
            self.load_alarms()
            from kivy.app import App
            from src.settings import SCREEN
            select_alarm_screen = App.get_running_app().get_screen(SCREEN.SELECT_ALARM)
            select_alarm_screen.update_screen_state()
            return True
        
        except Exception as e:
            logger.error(f"Error deleting alarm: {e}")
            return False

    def on_task_expired_trigger_alarm(self, *args, **kwargs):
        """Default handler for on_task_expired_trigger_alarm event"""
        pass
