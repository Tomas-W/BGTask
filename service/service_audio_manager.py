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
        self._lock = threading.Lock()
        
        # Thread control using Events
        self._alarm_stop_event = threading.Event()
        self._vibrate_stop_event = threading.Event()
        self._alarm_thread: threading.Thread | None = None
        self._vibrate_thread: threading.Thread | None = None
    
    def _get_java_class(self, class_name: str) -> Any:
        """Lazy load Java classes"""
        with self._lock:
            if class_name not in self._java_classes:
                self._java_classes[class_name] = autoclass(class_name)
        
        return self._java_classes[class_name]
    
    def play(self, path):
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
            logger.error(f"Error playing audio: {e}")
            return False
    
    def stop(self):
        """Stop audio playback"""
        try:
            if not self.media_player:
                return True
            
            if self.is_playing():
                self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            return True
            
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return False
    
    def is_playing(self):
        """Check if audio is currently playing"""
        try:
            return self.media_player and self.media_player.isPlaying()
        
        except Exception as e:
            logger.error(f"Error checking playback status: {e}")
            return False

    def vibrate(self, duration=1000):
        """Vibrate the device for a specified duration"""
        try:
            if not self.vibrator:
                # Get the Android Context from the service
                Context = self._get_java_class("android.content.Context")
                # Use service context instead of activity
                self.vibrator = self.service.getSystemService(Context.VIBRATOR_SERVICE)
            
            if self.vibrator:
                # Just vibrate for the specified duration
                self.vibrator.vibrate(duration)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error vibrating device: {e}")
            return False
    
    def _alarm_loop(self):
        """Background thread for continuously playing an alarm"""
        logger.debug("Starting alarm loop")
        while not self._alarm_stop_event.is_set() and self.task and self.task.keep_alarming:
            try:
                if not self.is_playing():
                    path = self.get_audio_path(self.task.alarm_name)
                    if path:
                        self.play(path)
                        logger.debug("Started alarm playback")
                    else:
                        logger.error("Could not find alarm path")
                        break
                # Wait for stop event with timeout
                if self._alarm_stop_event.wait(2):  # Returns True if event is set
                    break
            
            except Exception as e:
                logger.error(f"Error in alarm loop: {e}")
                break
        logger.debug("Alarm loop ended")
    
    def _vibrate_loop(self):
        """Background thread for continuously vibrating the device"""
        logger.debug("Starting vibrate loop")
        while not self._vibrate_stop_event.is_set() and self.task and self.task.vibrate and self.task.keep_alarming:
            try:
                self.vibrate(1000)
                # Wait for stop event with timeout
                if self._vibrate_stop_event.wait(2):  # Returns True if event is set
                    break
            
            except Exception as e:
                logger.error(f"Error in vibrate loop: {e}")
                break
        logger.debug("Vibrate loop ended")
    
    def trigger_alarm(self, task, *args, **kwargs):
        """Trigger the alarm for the current task"""
        logger.debug("Triggering alarm for task")
        self.stop_playing_alarm()
        self.stop_vibrating()

        with self._lock:
            # Clear any existing stop events
            self._alarm_stop_event.clear()
            self._vibrate_stop_event.clear()
            
            self.task = task
            play_alarm = task.alarm_name
            audio_path = self.get_audio_path(task.alarm_name)
            vibrate = task.vibrate
            keep_alarming = task.keep_alarming
            
            # Start alarm if needed
            if play_alarm and keep_alarming:
                self._alarm_thread = threading.Thread(target=self._alarm_loop)
                self._alarm_thread.daemon = True
                self._alarm_thread.start()
                logger.debug("Started alarm thread")
            # One-time alarm
            elif audio_path:
                self.play(audio_path)
                logger.debug("Started one-time alarm playback")
            
            # Start vibration if needed
            if vibrate and keep_alarming:
                self._vibrate_thread = threading.Thread(target=self._vibrate_loop)
                self._vibrate_thread.daemon = True
                self._vibrate_thread.start()
                logger.debug("Started vibrate thread")
            # One-time vibration
            elif vibrate:
                self.vibrate(2000)
                logger.debug("Triggered one-time vibration")
    
    def stop_playing_alarm(self, *args, **kwargs):
        """Stop the alarm playback and cleanup resources"""
        logger.debug("Stopping alarm playback")
        with self._lock:
            self._alarm_stop_event.set()
        
        if self._alarm_thread and self._alarm_thread.is_alive():
            self._alarm_thread.join(timeout=1)
        
        self.stop()
        logger.debug("Alarm playback stopped")
    
    def stop_vibrating(self, *args, **kwargs):
        """Stop vibration and cleanup vibrator resources"""
        logger.debug("Stopping vibration")
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
    
    def stop_alarm_vibrating(self, *args, **kwargs):
        """Stop both alarm and vibration"""
        logger.debug("Stopping all audio and vibration")
        
        with self._lock:
            # Signal both threads to stop
            self._alarm_stop_event.set()
            self._vibrate_stop_event.set()
        
        if self._alarm_thread and self._alarm_thread.is_alive():
            self._alarm_thread.join(timeout=1)
        if self._vibrate_thread and self._vibrate_thread.is_alive():
            self._vibrate_thread.join(timeout=1)
        
        self.stop()
        try:
            if self.vibrator:
                self.vibrator.cancel()
                self.vibrator = None
        except Exception as e:
            logger.error(f"Error stopping vibration: {e}")
        
        with self._lock:
            self.task = None
        
        # Check if threads are still alive
        if (self._alarm_thread and self._alarm_thread.is_alive()) or \
           (self._vibrate_thread and self._vibrate_thread.is_alive()):
            logger.error("Failed to stop all alarms/vibrations")
        
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
