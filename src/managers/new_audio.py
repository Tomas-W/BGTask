import threading
import os

from jnius import autoclass  # type: ignore

from src.managers.device.device_manager import DM
from src.settings import DIR
from src.managers.tasks.task_manager_utils import Task

from src.utils.logger import logger

from kivy.core.audio import SoundLoader


class AudioManager:
    """Manages audio playback and recording"""
    def __init__(self):
        self.recordings_dir: str = DM.get_storage_path(DIR.RECORDINGS)
        DM.validate_dir(self.recordings_dir)

        self.alarms_dir: str = DM.get_storage_path(DIR.ALARMS)
        DM.validate_dir(self.alarms_dir)

        if DM.is_android():
            self.audio_player = AndroidAudioPlayer()
            self.audio_recorder = AndroidAudioRecorder()
            self.audio_player.bind_audio_manager(self)

        self.task: Task | None = None

        # Threading controls
        self._lock = threading.Lock()
        self._alarm_stop_event = threading.Event()
        self._vibrate_stop_event = threading.Event()
        self._alarm_thread = None
        self._vibrate_thread = None

    def trigger_alarm(self, task, *args, **kwargs) -> bool:
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
            
            self.task = task
            play_alarm = task.alarm_name
            vibrate = task.vibrate
            keep_alarming = task.keep_alarming

            if not play_alarm:
                logger.trace("No alarm name set, skipping alarm playback")
                return False

            # Set alarm path
            self.current_alarm_path = self.get_audio_path(task.alarm_name)
            if not self.current_alarm_path:
                logger.error(f"Could not find alarm audio: {task.alarm_name}")
                return False

            # Continuous alarm
            if play_alarm and keep_alarming:
                self._alarm_thread = threading.Thread(target=self._alarm_loop)
                self._alarm_thread.daemon = True
                self._alarm_thread.start()
                logger.trace("Started continuous alarm playback")
            # One-time alarm
            elif self.current_alarm_path:
                self.audio_player.play(self.current_alarm_path)
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
        while not self._alarm_stop_event.is_set() and self.task and self.task.keep_alarming:
            try:
                if not self.audio_player.is_playing():
                    if not self.audio_player.play(self.current_alarm_path):
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
        alarm_path = os.path.join(self.alarms_dir, f"{name}.wav")
        if os.path.exists(alarm_path):
            return alarm_path
        
        # Check user recordings
        recording_path = os.path.join(self.recordings_dir, f"{name}.wav")
        if os.path.exists(recording_path):
            return recording_path
            
        logger.error(f"Audio file not found for name: {name}")
        return None

    def __del__(self):
        """Cleanup when the manager is destroyed"""
        self.stop_alarm()



from jnius import autoclass  # type: ignore
from kivy.clock import Clock

from src.utils.logger import logger


class AndroidAudioPlayer:
    """Android audio player for playback and vibration"""
    def __init__(self):
        self.audio_manager = None
        self.media_player = None
        self.vibrator = None
        self._java_classes = {}

    def bind_audio_manager(self, audio_manager):
        """Bind the main audio manager for state management"""
        self.audio_manager = audio_manager

    def _get_java_class(self, class_name: str):
        """Lazy load Java classes only when needed"""
        if class_name not in self._java_classes:
            self._java_classes[class_name] = autoclass(class_name)
        return self._java_classes[class_name]

    def play(self, path: str) -> bool:
        """Play audio file using Android MediaPlayer"""
        try:
            self.stop()
            
            MediaPlayer = self._get_java_class("android.media.MediaPlayer")
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(path)
            self.media_player.prepare()
            self.media_player.start()
            logger.trace(f"Started Android audio playback: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio on Android: {e}")
            return False

    def stop(self) -> bool:
        """Stop any playing audio"""
        try:
            if not self.media_player or not self.media_player.isPlaying():
                return True

            self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            logger.trace("Stopped Android audio playback")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Android playback: {e}")
            return False

    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        try:
            return self.media_player and self.media_player.isPlaying()
        
        except Exception as e:
            logger.error(f"Error checking playback status on Android: {e}")
            return False

    def vibrate(self, *args, **kwargs) -> bool:
        """Vibrate the device using Android's Vibrator service"""
        try:
            if not self.vibrator:
                # Get the Android Context
                Context = self._get_java_class("android.content.Context")
                PythonActivity = self._get_java_class("org.kivy.android.PythonActivity")
                activity = PythonActivity.mActivity
                
                # Get the Vibrator service
                self.vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
            
            if self.vibrator:
                # Vibrate for 1 second (1000ms)
                self.vibrator.vibrate(1000)
                if self.audio_manager and self.audio_manager.keep_alarming:
                    Clock.schedule_once(self.vibrate, 2)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error vibrating on Android: {e}")
            return False



from jnius import autoclass  # type: ignore

from src.utils.logger import logger


class AndroidAudioRecorder:
    """Android audio recorder for capturing audio"""
    def __init__(self):
        self.recorder = None
        self.recording = False
        self.current_path = None
        self._java_classes = {}

    def _get_java_class(self, class_name: str):
        """Lazy load Java classes only when needed"""
        if class_name not in self._java_classes:
            self._java_classes[class_name] = autoclass(class_name)
        return self._java_classes[class_name]

    def setup_recording(self, path: str) -> bool:
        """Configure the recorder for a new recording session"""
        try:
            # Lazy load Java classes only when needed
            MediaRecorder = self._get_java_class("android.media.MediaRecorder")
            AudioSource = self._get_java_class("android.media.MediaRecorder$AudioSource")
            OutputFormat = self._get_java_class("android.media.MediaRecorder$OutputFormat")
            AudioEncoder = self._get_java_class("android.media.MediaRecorder$AudioEncoder")
            
            # Reset any existing recorder
            if self.recorder:
                self.recorder.release()
            
            self.recorder = MediaRecorder()
            self.recorder.setAudioSource(AudioSource.MIC)
            
            # no direct support for .wav
            # use 3GP instead
            self.recorder.setOutputFormat(OutputFormat.THREE_GPP)
            self.recorder.setAudioEncoder(AudioEncoder.AMR_NB)
            
            self.recorder.setOutputFile(path)
            self.recorder.prepare()
            self.current_path = path
            return True
        
        except Exception as e:
            logger.error(f"Error setting up Android recorder: {e}")
            return False

    def start_recording(self) -> bool:
        """Start recording audio"""
        try:
            if not self.recorder:
                logger.error("Android recorder not found, setup recording first")
                return False
                
            if self.recording:
                logger.error(f"Already recording: {self.current_path}")
                return False
            
            self.recorder.start()
            self.recording = True
            logger.trace(f"Android recording started: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting Android recorder: {e}")
            return False

    def stop_recording(self) -> bool:
        """Stop the recording and release resources"""
        try:
            if not self.recorder:
                logger.error("Android recorder not set-up")
                return False
                
            if not self.recording:
                logger.error("Not recording Android audio, nothing to stop")
                return False
            
            self.recorder.stop()
            self.recorder.release()
            self.recorder = None
            self.recording = False
            logger.trace(f"Android recording stopped and saved: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Android recorder: {e}")
            self.recording = False
            return False

    def release(self) -> bool:
        """Release recorder resources without stopping (for cleanup)"""
        try:
            if self.recorder:
                self.recorder.release()
                self.recorder = None
            
            self.recording = False
            return True
        
        except Exception as e:
            logger.error(f"Error releasing Android recorder resources: {e}")
            return False

    
class WindowsAudioPlayer:
    """Windows audio player for playback"""
    def __init__(self):
        self.audio_manager = None
        self.sound = None

    def bind_audio_manager(self, audio_manager):
        self.audio_manager = audio_manager

    def play(self, path: str) -> bool:
        """Play audio file using Kivy SoundLoader"""
        try:
            self.stop()
            
            sound = SoundLoader.load(path)
            if sound:
                sound.play()
                self.sound = sound
                logger.debug(f"Started Windows audio playback: {path}")
                return True
            
            else:
                logger.error(f"Could not load sound: {path}")
                return False
        
        except Exception as e:
            logger.error(f"Error playing audio on Windows: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop any playing audio"""
        try:
            if not self.sound or not self.sound.state == "play":
                return True
            
            self.sound.stop()
            self.sound = None
            logger.debug("Stopped Windows audio playback")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping audio on Windows: {e}")
            return False
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        try:
            return self.sound and self.sound.state == "play"
        
        except Exception as e:
            logger.error(f"Error checking playback status on Windows: {e}")
            return False

    def vibrate(self, *args, **kwargs) -> bool:
        """Stub implementation for Windows - vibration not supported"""
        return True


try:
    import pyaudio
    import wave
except ImportError:
    pass

from src.utils.logger import logger


class WindowsAudioRecorder:
    """Windows audio recorder for capturing audio"""
    def __init__(self):
        self.current_path = None
        self.recording = False
        self.stream = None
        self.frames = []
        self.pa = None
        
        try:            
            self.pyaudio = pyaudio
            self.wave = wave
            self.pa = pyaudio.PyAudio()
        
        except Exception as e:
            logger.error(f"Error initializing PyAudio: {e}")

    def setup_recording(self, path: str) -> bool:
        """Configure the recorder for a new recording session"""        
        try:
            self.current_path = path
            self.frames = []
            return True
        
        except Exception as e:
            logger.error(f"Error setting up Windows recorder: {e}")
            return False
    
    def start_recording(self) -> bool:       
        try:
            if self.recording:
                logger.error(f"Already recording: {self.current_path}")
                return False
            
            self.recording = True
            self.frames = []

            def callback(in_data, frame_count, time_info, status):
                if self.recording:
                    self.frames.append(in_data)
                    return (in_data, self.pyaudio.paContinue)
                return (in_data, self.pyaudio.paComplete)
            
            # Open stream using callback
            self.stream = self.pa.open(
                format=self.pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024,
                stream_callback=callback
            )
            
            self.stream.start_stream()
            logger.debug(f"Windows recording started: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting Windows recording: {e}")
            self.recording = False
            return False
    
    def stop_recording(self) -> bool:
        try:
            if not self.recording:
                logger.error("Not recording Windows audio, nothing to stop")
                return False
            
            self.recording = False
            
            # Stop and close stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                logger.debug("Windows recording stopped")
            
            # Save recording to WAV file
            if self.frames and self.current_path:
                wf = self.wave.open(self.current_path, "wb")
                wf.setnchannels(1)
                wf.setsampwidth(self.pa.get_sample_size(self.pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b"".join(self.frames))
                wf.close()
                return True
            
            else:
                logger.error("No Windows audio data recorded")
                return False
        
        except Exception as e:
            logger.error(f"Error stopping Windows recording: {e}")
            return False

    def release(self) -> bool:
        """Release recorder resources without stopping (for cleanup)"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                
            if self.pa:
                self.pa.terminate()
                self.pa = None
                
            self.recording = False
            return True
        
        except Exception as e:
            logger.error(f"Error releasing Windows recorder resources: {e}")
            return False
