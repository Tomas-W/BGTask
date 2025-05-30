import threading
import os

from datetime import datetime

from managers.tasks.task_manager_utils import Task
from managers.device.device_manager import DM
from src.utils.logger import logger


class AudioManager:
    """
    Manages audio accross the App and Service.
    - Plays audio.
    - Vibrates.
    - Records audio.
    - Plays alarms.
    """
    def __init__(self, is_service: bool = False):
        if DM.is_android:
            from managers.audio.android_player import AndroidAudioPlayer
            self.audio_player = AndroidAudioPlayer()
            self.audio_player.bind_audio_manager(self)
            # Service does not require recorder
            if not is_service:
                from managers.audio.android_recorder import AndroidAudioRecorder
                self.audio_recorder = AndroidAudioRecorder()
        
        else:
            from managers.audio.windows_player import WindowsAudioPlayer
            from managers.audio.windows_recorder import WindowsAudioRecorder
            self.audio_player = WindowsAudioPlayer()
            self.audio_player.bind_audio_manager(self)

            self.audio_recorder = WindowsAudioRecorder()

        self.task: Task | None = None
        
        # Threading controls
        self._lock = threading.Lock()
        self._alarm_stop_event = threading.Event()
        self._vibrate_stop_event = threading.Event()
        self._alarm_thread = None
        self._vibrate_thread = None

    def trigger_alarm(self, *args, **kwargs) -> bool:
        """
        Starts a one-time or continuous alarm and vibrate depending on Task settings.
        Stops any running alarm or vibrate before starting new one.
        """
        logger.trace("Triggering alarm")
        self._stop_alarm_loop()
        self._stop_vibrate_loop()

        with self._lock:
            self._alarm_stop_event.clear()
            self._vibrate_stop_event.clear()
            self.task = kwargs.get("task") if "task" in kwargs else args[-1]
            if not self.task:
                logger.error("Error triggering alarm: No task provided")
                return False

            alarm_path = self.get_audio_path(self.task.alarm_name)
            play_alarm = self.task.alarm_name
            vibrate = self.task.vibrate
            keep_alarming = self.task.keep_alarming

            if not play_alarm and not vibrate:
                logger.trace("No alarm name or vibrate set, skipping alarm playback")
                return False
            
            # Continuous alarm
            if play_alarm and keep_alarming:
                self._alarm_thread = threading.Thread(target=self._alarm_loop)
                self._alarm_thread.daemon = True
                self._alarm_thread.start()
                logger.trace("Started continuous alarm playback")
            # One-time alarm
            elif alarm_path:
                self.audio_player.play(alarm_path)
                logger.trace("Started one-time alarm playback")
            
            # Continuous vibrate
            if vibrate and keep_alarming:
                self._vibrate_thread = threading.Thread(target=self._vibrate_loop)
                self._vibrate_thread.daemon = True
                self._vibrate_thread.start()
                logger.trace("Started continuous vibrate")
            # One-time vibrate
            elif vibrate:
                self.audio_player.vibrate()
                logger.trace("Started one-time vibrate")

            self.alarm_is_triggered = True
            return True

    def _alarm_loop(self) -> None:
        """Background thread for continuously playing an alarm."""
        path = None

        while not self._alarm_stop_event.is_set() and self.task and self.task.keep_alarming:
            try:
                if not path:
                    path = self.get_audio_path(self.task.alarm_name)
                    if not path:
                        logger.error(f"Could not find alarm audio: {self.task.alarm_name}")
                        break

                if not self.audio_player.is_playing():
                    if not self.audio_player.play(path):
                        logger.error("Failed to play alarm")
                        break
                
                self._alarm_stop_event.wait(2)
            
            except Exception as e:
                logger.error(f"Error in alarm loop: {e}")
                break
        
        logger.trace("Alarm loop ended")

    def _vibrate_loop(self) -> None:
        """Background thread for continuously vibrating."""
        while not self._vibrate_stop_event.is_set() and self.task and self.task.vibrate and self.task.keep_alarming:
            try:
                self.audio_player.vibrate()
                if self._vibrate_stop_event.wait(2):
                    break
            
            except Exception as e:
                logger.error(f"Error in vibrate loop: {e}")
                break
        
        logger.trace("Vibrate loop ended")

    def stop_alarm(self, *args, **kwargs) -> None:
        """Stop both alarm and vibrate if they are running."""
        self._stop_alarm_loop()
        self._stop_vibrate_loop()
        
        # Clear Task to break loops
        if (self._alarm_thread and self._alarm_thread.is_alive()) or \
           (self._vibrate_thread and self._vibrate_thread.is_alive()):
            with self._lock:
                self.task = None

    def _stop_alarm_loop(self) -> None:
        """Stop the alarm loop if it's running"""
        if not self._alarm_thread or not self._alarm_thread.is_alive():
            return
        
        try:
            with self._lock:
                self._alarm_stop_event.set()
            
            self._alarm_thread.join(timeout=1)
            self.audio_player.stop()
            self._alarm_thread = None
            logger.trace("Alarm loop stopped")
        
        except Exception as e:
            logger.error(f"Error stopping alarm loop: {e}")

    def _stop_vibrate_loop(self) -> None:
        """Stop the vibrate loop if it's running"""
        if not self._vibrate_thread or not self._vibrate_thread.is_alive():
            return
        
        try:
            with self._lock:
                self._vibrate_stop_event.set()
            
            self._vibrate_thread.join(timeout=1)
            self.audio_player.stop_vibrator()
            self._vibrate_thread = None
            logger.trace("Vibrate loop stopped")
        
        except Exception as e:
            logger.error(f"Error stopping vibrate loop: {e}")

    def get_audio_path(self, name: str) -> str | None:
        """
        Searches for the audio file in the alarms and recordings directories.
        Returns the path if found, otherwise returns None.
        """
        if not name:
            return None

        # Check default alarms
        alarm_path = os.path.join(DM.DIR.ALARMS, f"{name}{DM.EXT.WAV}")
        if os.path.exists(alarm_path):
            return alarm_path
        
        # Check user recordings
        recording_path = os.path.join(DM.DIR.RECORDINGS, f"{name}{DM.EXT.WAV}")
        if os.path.exists(recording_path):
            return recording_path
            
        logger.error(f"Audio file not found for name: {name}")
        return None

    def get_recording_path(self) -> tuple[str, str]:
        """
        Get the path and filename of a new recording.
        Format: ../{recordings_dir}/recording_HH_MM_SS.wav
        """
        name = "recording_"
        timestamp = datetime.now().strftime(DM.DATE.RECORDING)
        while True:
            path = os.path.join(DM.DIR.RECORDINGS, name + timestamp + DM.EXT.WAV)
            if os.path.exists(path):
                logger.warning(f"Recording file already exists: {path}")
                name += "_"
            else:
                break

        filename = f"{name}{timestamp}"
        path = os.path.join(DM.DIR.RECORDINGS, filename + DM.EXT.WAV)
        return path, filename