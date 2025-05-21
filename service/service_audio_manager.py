import os
import threading

from jnius import autoclass  # type: ignore
from typing import Any

from src.managers.tasks.task_manager_utils import Task
from service.service_utils import PATH

from src.utils.logger import logger


PythonService = autoclass("org.kivy.android.PythonService")


class ServiceAudioManager:
    """Manages playing audio and vibrations for the service"""
    def __init__(self):
        self.media_player: Any | None = None
        self._java_classes: dict[str, Any] = {}
        self.vibrator: Any | None = None
        self.service: Any = PythonService.mService

        self.task: Task | None = None
        self.alarms_dir: str = PATH.ALARMS_DIR
        self.recordings_dir: str = PATH.RECORDINGS_DIR
        
        # Thread synchronization lock
        self._lock: threading.Lock = threading.Lock()
        # Thread controls
        self._alarm_stop_event: threading.Event = threading.Event()
        self._vibrate_stop_event: threading.Event = threading.Event()
        self._alarm_thread: threading.Thread | None = None
        self._vibrate_thread: threading.Thread | None = None
    
    def trigger_alarm(self, task: Task, *args: Any, **kwargs: Any) -> None:
        """Trigger the audio and vibrate alarms for the current Task"""
        logger.debug("Triggering alarm")
        self._stop_alarm_loop()
        self._stop_vibrate_loop()

        with self._lock:
            self._alarm_stop_event.clear()
            self._vibrate_stop_event.clear()
            
            self.task = task
            play_alarm = task.alarm_name
            audio_path = self.get_audio_path(task.alarm_name)
            vibrate = task.vibrate
            keep_alarming = task.keep_alarming
            
            # Continuous alarm
            if play_alarm and keep_alarming:
                self._alarm_thread = threading.Thread(target=self._alarm_loop)
                self._alarm_thread.daemon = True
                self._alarm_thread.start()
                logger.debug("Started continuous alarm playback")
            # One-time alarm
            elif audio_path:
                self.play_audio(audio_path)
                logger.debug("Started one-time alarm playback")
            # No alarm set
            elif audio_path is None:
                logger.debug("No alarm set, skipping alarm playback")
            
            # Continuous vibrate
            if vibrate and keep_alarming:
                self._vibrate_thread = threading.Thread(target=self._vibrate_loop)
                self._vibrate_thread.daemon = True
                self._vibrate_thread.start()
                logger.debug("Started continuous vibrate")
            # One-time vibrate
            elif vibrate:
                self.vibrate(2000)
                logger.debug("Started one-time vibrate")
            # No vibrate set
            elif not vibrate:
                logger.debug("No vibrate set, skipping vibrate")
    
    def _alarm_loop(self) -> None:
        """Background thread for continuously playing an alarm"""
        path = None
        
        while not self._alarm_stop_event.is_set() and self.task and self.task.keep_alarming:
            try:
                # Get audio path
                if not path:
                    path = self.get_audio_path(self.task.alarm_name)
                    if not path:
                        logger.error("Task has no alarm set")
                        break
                
                # Play audio if not currently playing
                if not self.is_playing_audio():
                    if not self.play_audio(path):
                        logger.error("Failed to play alarm")
                        break
                
                # Small wait to prevent CPU spinning
                self._alarm_stop_event.wait(2)
            
            except Exception as e:
                logger.error(f"Error in alarm loop: {e}")
                break
        
        logger.debug("Alarm loop ended")
    
    def _vibrate_loop(self) -> None:
        """Background thread for continuously vibrating the device"""
        while not self._vibrate_stop_event.is_set() and self.task and self.task.vibrate and self.task.keep_alarming:
            try:
                self.vibrate(1000)
                if self._vibrate_stop_event.wait(2):
                    break
            
            except Exception as e:
                logger.error(f"Error in vibrate loop: {e}")
                break
        
        logger.debug("Vibrate loop ended")
    
    def stop_alarm_vibrate(self, *args: Any, **kwargs: Any) -> None:
        """Stop both alarm and vibrate if they are running"""
        # Stop each independently
        self._stop_alarm_loop()
        self._stop_vibrate_loop()
        
        # Clear Task to break loops if either was running
        if (self._alarm_thread and self._alarm_thread.is_alive()) or \
           (self._vibrate_thread and self._vibrate_thread.is_alive()):
            with self._lock:
                self.task = None
    
    def _stop_alarm_loop(self, *args: Any, **kwargs: Any) -> None:
        """Stop the alarm loop if it's running"""
        # Early return if no alarm thread or not running
        if not self._alarm_thread or not self._alarm_thread.is_alive():
            return
        
        try:
            with self._lock:
                self._alarm_stop_event.set()
            
            self._alarm_thread.join(timeout=1)
            self.stop_audio()
            self._alarm_thread = None
            logger.debug("Alarm loop stopped")
        
        except Exception as e:
            logger.error(f"Error stopping alarm loop: {e}")
    
    def _stop_vibrate_loop(self, *args: Any, **kwargs: Any) -> None:
        """Stop the vibrate loop if it's running"""
        # Early return if no vibrate thread or not running
        if not self._vibrate_thread or not self._vibrate_thread.is_alive():
            return
        
        try:
            with self._lock:
                self._vibrate_stop_event.set()
            
            self._vibrate_thread.join(timeout=1)
            self.stop_vibrator()
            self._vibrate_thread = None
            logger.debug("Vibrate loop stopped")
        
        except Exception as e:
            logger.error(f"Error stopping vibrate loop: {e}")
    
    def play_audio(self, path: str) -> bool:
        """Play an audio file"""
        try:
            self.stop_audio()
            MediaPlayer = self._get_java_class("android.media.MediaPlayer")
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(path)
            self.media_player.prepare()
            self.media_player.start()
            logger.debug(f"Started playback: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            return False
    
    def stop_audio(self) -> bool:
        """Stop currently playing audio"""
        try:
            if not self.media_player:
                return True
            
            if self.is_playing_audio():
                self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            logger.debug("Stopped playback")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return False
    
    def vibrate(self, duration: int = 1000) -> bool:
        """Vibrate the device for a specified duration"""
        try:
            if not self.vibrator:
                Context = self._get_java_class("android.content.Context")
                self.vibrator = self.service.getSystemService(Context.VIBRATOR_SERVICE)
            
            if self.vibrator:
                self.vibrator.vibrate(duration)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error vibrating device: {e}")
            return False
    
    def stop_vibrator(self) -> bool:
        """Stop the vibrator and reset it"""
        try:
            if self.vibrator:
                self.vibrator.cancel()
                self.vibrator = None
            logger.debug("Vibration stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping vibration: {e}")
            return False
    
    def is_playing_audio(self) -> bool:
        """Returns True if audio is currently playing, otherwise returns False"""
        try:
            return self.media_player and self.media_player.isPlaying()
        
        except Exception as e:
            logger.error(f"Error checking audio playback status: {e}")
            return False
    
    def get_audio_path(self, name: str | None) -> str | None:
        """
        Searches for the file in the alarms and recordings directories.
        Returns the path if found, otherwise returns None.
        """
        if name is None:
            return None

        # Check default alarms
        alarm_path = os.path.join(self.alarms_dir, f"{name}.wav")
        if os.path.exists(alarm_path):
            return alarm_path
        
        # Check user recordings
        recording_path = os.path.join(self.recordings_dir, f"{name}.wav")
        if os.path.exists(recording_path):
            return recording_path
            
        logger.error(f"Audio file not found for name: {name}")
        return None
    
    def _get_java_class(self, class_name: str) -> Any:
        """Lazy load Java classes"""
        with self._lock:
            if class_name not in self._java_classes:
                self._java_classes[class_name] = autoclass(class_name)
        
        return self._java_classes[class_name]

    def __del__(self) -> None:
        self.stop_alarm_vibrate()
