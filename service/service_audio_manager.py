import os
import threading
import time

from jnius import autoclass  # type: ignore
from typing import Any

from src.managers.tasks.task_manager_utils import Task
from service.service_logger import logger
from service.service_utils import PATH

__all__ = ["ServiceAudioManager"]

PythonService = autoclass("org.kivy.android.PythonService")


class ServiceAudioManager:
    """Manages playing audio and vibrations for the service"""
    def __init__(self):
        self.media_player: Any | None = None
        self._java_classes: dict[str, Any] = {}
        self.vibrator: Any | None = None
        self.service = PythonService.mService

        self.task: Task | None = None
        self.alarms_dir: str = PATH.ALARMS_DIR
        self.recordings_dir: str = PATH.RECORDINGS_DIR
        
        # Thread synchronization lock
        self._lock: threading.Lock = threading.Lock()
        
        # Thread control using Events
        self._alarm_stop_event: threading.Event = threading.Event()
        self._vibrate_stop_event: threading.Event = threading.Event()
        self._alarm_thread: threading.Thread | None = None
        self._vibrate_thread: threading.Thread | None = None
    
    def _get_java_class(self, class_name: str) -> Any:
        """Lazy load Java classes"""
        with self._lock:
            if class_name not in self._java_classes:
                self._java_classes[class_name] = autoclass(class_name)
        
        return self._java_classes[class_name]
    
    def play(self, path: str) -> bool:
        """Play an audio file"""
        try:
            self.stop()
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
    
    def stop(self) -> bool:
        """Stop currently playing audio"""
        try:
            if not self.media_player:
                return True
            
            if self.is_playing():
                self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            logger.debug("Stopped playback")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return False
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        try:
            return self.media_player and self.media_player.isPlaying()
        
        except Exception as e:
            logger.error(f"Error checking playback status: {e}")
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
    
    def _alarm_loop(self) -> None:
        """Background thread for continuously playing an alarm"""
        logger.debug("Starting alarm loop")
        path = None
        
        while not self._alarm_stop_event.is_set() and self.task and self.task.keep_alarming:
            try:
                # Get audio path if not already set
                if not path:
                    path = self.get_audio_path(self.task.alarm_name)
                    if not path:
                        logger.error("Task has no alarm set")
                        break
                
                # Play audio if not currently playing
                if not self.is_playing():
                    if not self.play(path):
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
        logger.debug("Starting vibrate loop")
        while not self._vibrate_stop_event.is_set() and self.task and self.task.vibrate and self.task.keep_alarming:
            try:
                self.vibrate(1000)
                if self._vibrate_stop_event.wait(2):
                    break
            
            except Exception as e:
                logger.error(f"Error in vibrate loop: {e}")
                break
        
        logger.debug("Vibrate loop ended")
    
    def trigger_alarm(self, task: Task, *args: Any, **kwargs: Any) -> None:
        """Trigger the audio and vibration alarms for the current Task"""
        self.stop_playing_alarm()
        self.stop_vibrating()

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
            # One-time alarm
            elif audio_path:
                self.play(audio_path)
                logger.debug("Started one-time alarm playback")
            
            # Continuous vibration
            if vibrate and keep_alarming:
                self._vibrate_thread = threading.Thread(target=self._vibrate_loop)
                self._vibrate_thread.daemon = True
                self._vibrate_thread.start()
            # One-time vibration
            elif vibrate:
                self.vibrate(2000)
                logger.debug("Started one-time vibration")
    
    def stop_playing_alarm(self, *args: Any, **kwargs: Any) -> None:
        """Stop the alarm playback"""
        with self._lock:
            self._alarm_stop_event.set()
        
        if self._alarm_thread and self._alarm_thread.is_alive():
            self._alarm_thread.join(timeout=1)
        
        self.stop()
        logger.debug("Alarm playback stopped")
    
    def stop_vibrating(self, *args: Any, **kwargs: Any) -> bool:
        """Stop vibration the device"""
        with self._lock:
            self._vibrate_stop_event.set()
        
        if self._vibrate_thread and self._vibrate_thread.is_alive():
            self._vibrate_thread.join(timeout=1)
        
        try:
            if self.vibrator:
                self.vibrator.cancel()
                self.vibrator = None
            logger.debug("Vibration stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping vibration: {e}")
            return False
    
    def stop_alarm_vibrating(self, *args: Any, **kwargs: Any) -> None:
        """Stop both alarm and vibration"""
        logger.debug("Stopping all audio and vibration")
        with self._lock:
            # Clear task reference to break loop conditions
            self.task = None
        
        # Stop both alarm and vibration
        self.stop_playing_alarm()
        self.stop_vibrating()
        
        # Check if everything stopped properly
        if (self._alarm_thread and self._alarm_thread.is_alive()) or \
           (self._vibrate_thread and self._vibrate_thread.is_alive()):
            logger.error("Failed to stop all alarms/vibrations")
        else:
            logger.debug("All threads stopped successfully")
            self._alarm_thread = None
            self._vibrate_thread = None
        
        logger.debug("Alarm and vibration stopped")
    
    def get_audio_path(self, name: str) -> str | None:
        """
        Searches for the file in the alarms and recordings directories.
        Returns the path if found, otherwise returns None.
        """
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
