try:
    from jnius import autoclass  # type: ignore
except ImportError:
    pass

from src.utils.logger import logger


class AndroidAudioPlayer:
    """Android-specific audio implementation for recording and playback."""
    def __init__(self):
        self.recorder = None
        self.media_player = None
        self.recording = False
        self.current_path = None
        
        # Cache for Java classes
        self._java_classes = {}
        self.vibrator = None
        
    def _get_java_class(self, class_name):
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
        """Stop the recording and release resources."""
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
        """
        Stop any playing audio.
        """
        try:
            if not self.media_player or not self.media_player.isPlaying():
                return True

            self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            logger.trace(f"Stopped Android audio playback: {self.current_path}")
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
    
    def release(self) -> bool:
        """Release resources without stopping (for cleanup)."""
        try:
            if self.recorder:
                self.recorder.release()
                self.recorder = None
            
            self.recording = False
            self.stop()
            return True
        
        except Exception as e:
            logger.error(f"Error releasing Android resources: {e}")
            return False
    
    def vibrate(self) -> bool:
        """Vibrate the device using Android's Vibrator service."""
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
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error vibrating on Android: {e}")
            return False
