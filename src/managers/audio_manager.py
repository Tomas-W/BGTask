import os

from datetime import datetime

from src.settings import PATH, PLATFORM, EXT


class AudioManager:
    """
    Manages audio across the application.
    Loads the appropriate recorder based on the platform.
    """
    def __init__(self):
        from kivy.app import App
        self.logger = App.get_running_app().logger
        self.is_android = self.check_is_android()
        self.is_windows = self.check_is_windows()
        
        # Alarms directory
        self.alarm_dir = self._get_alarm_dir()
        self.validate_alarm_dir()
        
        # Platform-specific recorder
        if self.is_android:
            self.recorder = AndroidAudioRecorder()
            self.logger.debug("Using Android-specific audio recorder")
        elif self.is_windows:
            self.recorder = WindowsAudioRecorder()
            self.logger.debug("Using Windows-specific audio recorder")
        
        # Alarms
        self.alarms = {}
        self.load_alarms()
        self.selected_alarm_name = None
        self.selected_alarm_path = None
        
        # States
        self.is_recording = False
        self.has_recording_permission = self.check_recording_permission()
    
    def check_is_android(self):
        """Returns whether the app is running on Android."""
        from kivy.utils import platform
        return platform == PLATFORM.ANDROID
    
    def check_is_windows(self):
        """Returns whether the app is running on Windows."""
        import platform as py_platform
        return py_platform.system() == "Windows"
    
    def check_recording_permission(self):
        """Returns whether Android RECORD_AUDIO permission is granted."""
        if not self.is_android:
            return True
        
        try:
            from android.permissions import check_permission, Permission  # type: ignore
            return check_permission(Permission.RECORD_AUDIO)
            
        except ImportError:
            self.logger.error("Android permissions module not available. Ensure this is running on Android.")
            return False
        except AttributeError:
            self.logger.error("Permission.RECORD_AUDIO not found. Check Kivy's Android permissions module.")
            return False
        except RuntimeError as e:
            self.logger.error(f"Runtime error: {e}. Ensure request_permissions is called from the main thread.")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while requesting permissions: {e}")
            return False

    def request_android_recording_permissions(self):
        """Displays a dialog to request Android RECORD_AUDIO permissions."""
        if not self.is_android:
            return
            
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions(
                [Permission.RECORD_AUDIO],
                self.recording_permission_callback
            )
        except ImportError:
            self.logger.error("Android permissions module not available. Ensure this is running on Android.")
        except AttributeError:
            self.logger.error("Permission.RECORD_AUDIO not found. Check Kivy's Android permissions module.")
        except RuntimeError as e:
            self.logger.error(f"Runtime error: {e}. Ensure request_permissions is called from the main thread.")
        except Exception as e:
            self.logger.error(f"Unexpected error while requesting permissions: {e}")
    
    def recording_permission_callback(self, permissions, results):
        """Handles recording permission response."""
        if all(results):  # All permissions granted
            self.logger.debug(f"Permissions {permissions} granted")
            self.has_recording_permission = True
        else:
            self.logger.debug(f"Permissions {permissions} denied")
            self.has_recording_permission = False
    
    def _get_alarm_dir(self):
        """Get the directory path where the alarms are stored."""
        if self.is_android:
            try:
                from android.storage import app_storage_path  # type: ignore
                return os.path.join(app_storage_path(), PATH.ALARMS)
            except ImportError:
                self.logger.error("Android storage module not available.")
                return os.path.join(os.path.expanduser("~"), PATH.ALARMS)
        else:
            return os.path.join(PATH.ALARMS)
    
    def validate_alarm_dir(self):
        """Validate the alarm directory."""
        if not os.path.isdir(self.alarm_dir):
            try:
                os.makedirs(self.alarm_dir, exist_ok=True)
                self.logger.debug(f"Created alarm directory: {self.alarm_dir}")
            except PermissionError:
                self.logger.error(f"Permission denied: Cannot create directory {self.alarm_dir}. Check app permissions.")
            except FileNotFoundError:
                self.logger.error(f"Invalid path: {self.alarm_dir} does not exist.")
            except OSError as e:
                self.logger.error(f"OS error while creating {self.alarm_dir}: {e}")
    
    def get_recording_path(self):
        """Get the path and filename of the just started recording."""
        filename = f"recording_{datetime.now().strftime('%H-%M-%S')}"
        path = os.path.join(self.alarm_dir, filename + EXT.WAV)
        return path, filename
    
    def load_alarms(self):
        """Load the alarm files from the storage path."""
        if not os.path.exists(self.alarm_dir):
            self.logger.warning(f"Alarm directory not found: {self.alarm_dir}")
            return
            
        alarms = {}
        for file in os.listdir(self.alarm_dir):
            if file.endswith(EXT.WAV):
                alarms[file.split(".")[0]] = os.path.join(self.alarm_dir, file)
        self.alarms = alarms
        self.logger.debug(f"Loaded {len(alarms)} alarms")
    
    def name_to_path(self, name):
        """Convert an alarm name to a path."""
        return os.path.join(self.alarm_dir, f"{name}{EXT.WAV}")
    
    def path_to_name(self, path):
        """Convert a path to an alarm name."""
        return os.path.basename(path).split(".")[0]

    def set_alarm_name(self, name=None, path=None):
        """Set the name of the alarm"""
        if path:
            self.selected_alarm_name = self.path_to_name(path)
        elif name:
            self.selected_alarm_name = name
        else:
            self.logger.error("Either name or path must be provided")
            raise ValueError("Either name or path must be provided")
    
    def set_alarm_path(self, path=None, name=None):
        """Set the path of the alarm."""
        if path:
            self.selected_alarm_path = path
        elif name:
            self.selected_alarm_path = self.name_to_path(name)
        else:
            self.logger.error("Either path or name must be provided")
            raise ValueError("Either path or name must be provided")

    def start_recording(self):
        """Start recording audio using the appropriate method based on the platform."""
        if not self.recorder:
            self.logger.error("No recorder available")
            return False
            
        if self.is_android and not self.has_recording_permission:
            self.logger.debug("Requesting recording permissions")
            self.request_android_recording_permissions()
            return False
        
        path, filename = self.get_recording_path()
        self.logger.debug(f"Starting recording: {path}")
        
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
                    self.logger.error("Failed to start recording")
            else:
                self.logger.error("Failed to setup recorder")
            
            return False
        except Exception as e:
            self.logger.error(f"Recording error: {e}")
            return False

    def stop_recording(self):
        """Stop recording audio using the appropriate method based on the platform."""
        if not self.recorder:
            self.logger.error("No recorder available for this platform")
            return False
            
        success = False
        
        try:
            self.logger.debug("Stopping recording")
            if self.is_android:
                success = self.recorder.stop_recording_android()
            else:  # Windows
                success = self.recorder.stop_recording_desktop()
            
            if success and self.selected_alarm_path:
                try:
                    if self.is_windows:
                        import time
                        time.sleep(0.5)
                        
                    # Verify the file
                    if os.path.exists(self.selected_alarm_path):
                        with open(self.selected_alarm_path, "rb") as f:
                            audio_data = f.read(1024)
                        # Reload alarms to add new recording
                        self.load_alarms()
                        self.logger.debug(f"Successfully saved recording to {self.selected_alarm_path}")
                    else:
                        self.logger.error(f"File not found after recording: {self.selected_alarm_path}")
                        success = False
                except FileNotFoundError:
                    self.logger.error(f"File not found: {self.selected_alarm_path}")
                    success = False
                except Exception as e:
                    self.logger.error(f"Error reading audio data: {e}")
                    success = False
            
            self.is_recording = False
            return success
        
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            self.is_recording = False
            return False


class AndroidAudioRecorder:
    """Android-specific audio recording implementation."""
    def __init__(self):
        from kivy.app import App
        self.logger = App.get_running_app().logger
        self.recorder = None
        
    def setup(self, path):
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
            self.logger.error(f"Error setting up Android recorder: {e}")
            return False

    def start_recording_android(self):
        """Start the recording."""
        try:
            if not self.recorder:
                return False
            
            self.recorder.start()
            return True
        
        except Exception as e:
            self.logger.error(f"Error starting Android recorder: {e}")
            return False

    def stop_recording_android(self):
        """Stop the recording and release resources."""
        try:
            if not self.recorder:
                return False
            
            self.recorder.stop()
            self.recorder.release()
            self.recorder = None
            return True
        
        except Exception as e:
            self.logger.error(f"Error stopping Android recorder: {e}")
            return False
            
    def release(self):
        """Release resources without stopping (for cleanup)."""
        try:
            if self.recorder:
                self.recorder.release()
                self.recorder = None
        
        except Exception as e:
            self.logger.error(f"Error releasing Android recorder: {e}")


class WindowsAudioRecorder:
    """Windows-specific audio recording implementation using PyAudio."""
    def __init__(self):
        from kivy.app import App
        self.logger = App.get_running_app().logger
        self.current_path = None
        self.recording = False
        self.stream = None
        self.frames = []
        self.pa = None
        
        try:
            import pyaudio
            import wave
            self.pyaudio = pyaudio
            self.wave = wave
            self.pa = pyaudio.PyAudio()
            self.available = True
            self.logger.debug("Windows audio recorder initialized successfully with PyAudio")

        except ImportError as e:
            self.logger.error(f"PyAudio not available: {e}")
            self.available = False
        except Exception as e:
            self.logger.error(f"Error initializing PyAudio: {e}")
            self.available = False
    
    def setup(self, path):
        """Configure the recorder for a new recording session"""
        if not self.available:
            self.logger.error("Windows audio recorder not available - PyAudio missing")
            return False
            
        try:
            self.current_path = path
            self.frames = []
            self.logger.debug(f"Windows recorder setup with path: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting up Windows recorder: {e}")
            return False
    
    def start_recording_desktop(self):
        """Start recording using PyAudio"""
        if not self.available or not self.current_path:
            self.logger.error("Cannot start recording - recorder not available or path not set")
            return False
            
        try:
            if self.recording:
                self.logger.debug("Already recording")
                return True
            
            self.recording = True
            self.frames = []
            
            # Start recording in a thread to avoid blocking UI
            import threading
            
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
            self.logger.debug("Recording started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting Windows recording: {e}")
            self.recording = False
            return False
    
    def stop_recording_desktop(self):
        """Stop the recording"""
        if not self.available:
            return False
            
        try:
            self.logger.debug("Stopping Windows recording")
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
                self.logger.debug(f"Recording saved to {self.current_path}")
                return True
            else:
                self.logger.error("No audio data recorded")
                return False
            
        except Exception as e:
            self.logger.error(f"Error stopping Windows recording: {e}")
            return False
    
    def release(self):
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
            self.logger.error(f"Error releasing Windows audio resources: {e}")
            return False
