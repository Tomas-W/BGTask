import os

from kivy.app import App
from kivy.clock import Clock
from src.managers.device_manager import DM
from src.managers.audio.audio_manager_utils import AudioManagerUtils

from src.utils.logger import logger

from src.settings import EXT, DIR


class AudioManager(AudioManagerUtils):
    """
    Manages playing and recording audio through the application.
    Has a platform-specific audio player.
    All audio players have the same interface.
    """
    def __init__(self):
        super().__init__()
        if DM.is_android:
            from src.managers.audio.android_audio import AndroidAudioPlayer
            self.audio_player = AndroidAudioPlayer()
            self.audio_player.bind_audio_manager(self)
        
        elif DM.is_windows:
            from src.managers.audio.windows_audio import WindowsAudioPlayer
            self.audio_player = WindowsAudioPlayer()
            self.audio_player.bind_audio_manager(self)
        else:
            logger.error("No audio player loaded")
        
        app = App.get_running_app()
        app.task_manager.bind(on_task_expired_trigger_alarm=self.trigger_alarm)

        self.alarm_is_triggered: bool = False
        self.keep_alarming: bool | None = None
        self.audio_player.keep_alarming = self.keep_alarming
        self.current_alarm_path: str | None = None
        
        # Recordings
        self.recordings_dir: str = DM.get_storage_path(DIR.RECORDINGS)
        DM.validate_dir(self.recordings_dir)
        self.is_recording: bool = False

        # Alarms
        self.alarms_dir: str = DM.get_storage_path(DIR.ALARMS)
        DM.validate_dir(self.alarms_dir)
        self.alarms: dict[str, str] = {}
        self.load_alarms()
        self.selected_alarm_name: str | None = None
        self.selected_alarm_path: str | None = None
        
        # States
        self.is_recording: bool = False
        self.has_recording_permission: bool = DM.check_recording_permission()
    
    def trigger_alarm(self, *args, **kwargs):
        """
        Trigger the alarm for the given task.
        Handles audio playback and vibration if enabled.
        """
        if 1 == 1:
            print("1 IS INDEED EQUAL TO 1")
            return
        
        task = kwargs.get("task")
        if not task:
            logger.error("No task provided to trigger_alarm")
            return False
        
        if not task.alarm_name:
            logger.warning("Task has no alarm name set")
            return False
        
        # Stop any currently playing alarm first
        if self.is_playing():
            self.stop_playing_audio()
        
        self.keep_alarming = task.keep_alarming
        # Get alarm path and validate
        alarm_path = self.get_audio_path(task.alarm_name)
        if not alarm_path:
            logger.error(f"Could not find alarm audio: {task.alarm_name}")
            return False
        
        # Trigger vibration if enabled
        if task.vibrate:
            self.audio_player.vibrate()
        
        # Set up alarm state
        self.alarm_is_triggered = True
        self.current_alarm_path = alarm_path
        
        # Start playing and schedule replay
        if self.start_playing_audio(alarm_path):
            logger.info(f"Starting alarm: {alarm_path}")
            self.check_and_replay_alarm()
            return True
        return False
    
    def check_and_replay_alarm(self, *args, **kwargs):
        """Check if the alarm has finished playing and schedule the next play."""
        if not self.alarm_is_triggered or not self.keep_alarming:
            return
        
        if self.is_playing():
            Clock.schedule_once(self.check_and_replay_alarm, 2)
            return
        
        if self.keep_alarming:
            self.start_playing_audio(self.current_alarm_path)
            Clock.schedule_once(self.check_and_replay_alarm, 2)
            return
    
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
        
        sorted_alarms = sorted(alarms.items(), key=lambda x: x[0])
        self.alarms = dict(sorted_alarms)
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
        if DM.is_android and not self.has_recording_permission:
            DM.request_android_recording_permissions()
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

    def start_playing_audio(self, audio_path: str) -> bool:
        """
        Validates the alarm path and plays the audio file.
        """        
        if not audio_path:
            logger.error("No alarm selected to play")
            return False
        
        if not os.path.exists(audio_path):
            logger.error(f"Alarm file not found: {audio_path}")
            return False
        
        if not self.audio_player:
            logger.error("No audio player available")
            return False
            
        try:
            # Try playing the audio
            return self.audio_player.play(audio_path)
        
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
                return True
    
        logger.error(f"Alarm not found: {name} at {path}")
        return False
    
    def update_alarm_name(self, new_name: str) -> bool:
        """
        Updates the alarm name and path.
        """
        old_name = self.selected_alarm_name
        old_path = self.get_audio_path(old_name)
        if not old_path:
            logger.error(f"Alarm file not found: {old_name}")
            return False
        
        # Construct new path based on old file's location
        directory = os.path.dirname(old_path)
        new_path = os.path.join(directory, f"{new_name}{EXT.WAV}")
        
        # Rename the file
        os.rename(old_path, new_path)
        
        # Update internal state
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
        Deletes the alarm from the alarms and recordings directories.
        """
        path = self.get_audio_path(name)
        logger.trace(f"Called delete_alarm: {name} at {path}")
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
