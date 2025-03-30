import os

from src.managers.audio_manager_utils import AudioManagerUtils

from src.utils.logger import logger
from src.utils.platform import (device_is_android, device_is_windows, get_alarms_dir,
                                get_recordings_dir, validate_dir)

from src.settings import EXT


class AudioManager(AudioManagerUtils):
    """
    Manages audio across the application.
    """
    def __init__(self):
        self.is_android: bool = device_is_android()
        self.is_windows: bool = device_is_windows()
        
        # Recorder
        if self.is_android:
            self.recorder = AndroidAudioRecorder()
            logger.debug("Using Android-specific audio recorder")
        elif self.is_windows:
            self.recorder = WindowsAudioRecorder()
            logger.debug("Using Windows-specific audio recorder")
        
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
    
    def load_alarms(self):
        """Load the alarm files from the storage path."""
        alarms = {}
        # Recordings
        for file in os.listdir(self.recordings_dir):
            if file.endswith(EXT.WAV):
                alarms[file.split(".")[0]] = os.path.join(self.recordings_dir, file)

        # Default alarms
        for file in os.listdir(self.alarms_dir):
            if file.endswith(EXT.WAV):
                alarms[file.split(".")[0]] = os.path.join(self.alarms_dir, file)
        
        self.alarms: dict[str, str] = alarms
    
    def start_recording(self) -> bool:
        """Start recording audio using the appropriate method based on the platform."""
        if not self.recorder:
            logger.error("No recorder available")
            return False
        
        if self.is_android and not self.has_recording_permission:
            self.request_android_recording_permissions()
            return False
        
        path, filename = self.get_recording_path()
        try:
            if self.recorder.setup(path):
                if self.is_android:
                    success = self.recorder.start_recording_android()
                else:  # Windows
                    success = self.recorder.start_recording_desktop()
                
                if success:
                    self.is_recording = True
                    self.selected_alarm_name = filename
                    self.selected_alarm_path = path
                    return True
                else:
                    logger.error("Failed to start recording")
            else:
                logger.error("Failed to setup recorder")
            
            return False
        except Exception as e:
            logger.error(f"Recording error: {e}")
            return False
    
    def stop_recording(self) -> bool:
        """Stop recording audio using the appropriate method based on the platform."""
        if not self.recorder:
            logger.error("No recorder available for this platform")
            return False
        
        success = False
        try:
            if self.is_android:
                success = self.recorder.stop_recording_android()
            else:  # Windows
                success = self.recorder.stop_recording_desktop()
            
            if success and self.selected_alarm_path:
                try:
                    if self.is_windows:
                        import time
                        time.sleep(0.2)
                    
                    # Verify file
                    if os.path.exists(self.selected_alarm_path):
                        with open(self.selected_alarm_path, "rb") as f:
                            audio_data = f.read(1024)
                        # Reload alarms to add recording
                        self.load_alarms()
                    else:
                        logger.error(f"File not found after recording: {self.selected_alarm_path}")
                        success = False
                
                except FileNotFoundError:
                    logger.error(f"File not found: {self.selected_alarm_path}")
                    success = False
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    success = False
            
            self.is_recording = False
            return success
        
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            self.is_recording = False
            return False


class AndroidAudioRecorder:
    """Android-specific audio recording implementation."""
    def __init__(self):
        self.recorder = None
        
    def setup(self, path: str) -> bool:
        """Configure the recorder for a new recording session"""
        try:
            from jnius import autoclass  # type: ignore
            MediaRecorder = autoclass("android.media.MediaRecorder")
            AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
            OutputFormat = autoclass("android.media.MediaRecorder$OutputFormat")
            AudioEncoder = autoclass("android.media.MediaRecorder$AudioEncoder")
            
            self.recorder = MediaRecorder()
            self.recorder.setAudioSource(AudioSource.MIC)
            
            # no direct support for .wav
            # use 3GP instead
            self.recorder.setOutputFormat(OutputFormat.THREE_GPP)
            self.recorder.setAudioEncoder(AudioEncoder.AMR_NB)
            
            self.recorder.setOutputFile(path)
            self.recorder.prepare()
            return True
        
        except Exception as e:
            logger.error(f"Error setting up Android recorder: {e}")
            return False
    
    def start_recording_android(self) -> bool:
        try:
            if not self.recorder:
                return False
            
            self.recorder.start()
            return True
        
        except Exception as e:
            logger.error(f"Error starting Android recorder: {e}")
            return False
    
    def stop_recording_android(self) -> bool:
        """Stop the recording and release resources."""
        try:
            if not self.recorder:
                return False
            
            self.recorder.stop()
            self.recorder.release()
            self.recorder = None
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Android recorder: {e}")
            return False
    
    def release(self):
        """Release resources without stopping (for cleanup)."""
        try:
            if self.recorder:
                self.recorder.release()
                self.recorder = None
        
        except Exception as e:
            logger.error(f"Error releasing Android recorder: {e}")


class WindowsAudioRecorder:
    """Windows-specific audio recording implementation using PyAudio."""
    def __init__(self):
        self.current_path: str | None = None
        self.recording: bool = False
        self.stream: pyaudio.Stream | None = None
        self.frames: list[bytes] = []
        self.pa: pyaudio.PyAudio | None = None
        
        try:
            import pyaudio
            import wave
            self.pyaudio = pyaudio
            self.wave = wave
            self.pa = pyaudio.PyAudio()
            self.available = True
            logger.debug("Windows audio recorder initialized successfully with PyAudio")
        
        except ImportError as e:
            logger.error(f"PyAudio not available: {e}")
            self.available = False
        except Exception as e:
            logger.error(f"Error initializing PyAudio: {e}")
            self.available = False
    
    def setup(self, path: str) -> bool:
        """Configure the recorder for a new recording session."""
        if not self.available:
            logger.error("Windows audio recorder not available - PyAudio missing")
            return False
        
        try:
            self.current_path = path
            self.frames = []
            return True
        except Exception as e:
            logger.error(f"Error setting up Windows recorder: {e}")
            return False
    
    def start_recording_desktop(self) -> bool:
        if not self.available or not self.current_path:
            logger.error(f"Cannot start recording - recorder not available or path not set [{self.available=}, {self.current_path=}]")
            return False
        
        try:
            if self.recording:
                logger.debug("Already recording")
                return True
            
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
            return True
        
        except Exception as e:
            logger.error(f"Error starting Windows recording: {e}")
            self.recording = False
            return False
    
    def stop_recording_desktop(self) -> bool:
        if not self.available:
            return False
        
        try:
            if not self.recording:
                return False
            
            self.recording = False
            
            # Stop and close stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Save recording to WAV file
            if self.frames and self.current_path:
                wf = self.wave.open(self.current_path, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(self.pa.get_sample_size(self.pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b''.join(self.frames))
                wf.close()
                return True
            else:
                logger.error("No audio data recorded")
                return False
        
        except Exception as e:
            logger.error(f"Error stopping Windows recording: {e}")
            return False
    
    def release(self) -> bool:
        """Release any resources"""
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
            logger.error(f"Error releasing Windows audio resources: {e}")
            return False
