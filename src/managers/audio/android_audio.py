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
        
    def setup_recording(self, path: str) -> bool:
        """Configure the recorder for a new recording session"""
        try:
            MediaRecorder = autoclass("android.media.MediaRecorder")
            AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
            OutputFormat = autoclass("android.media.MediaRecorder$OutputFormat")
            AudioEncoder = autoclass("android.media.MediaRecorder$AudioEncoder")
            
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
            logger.debug(f"Setup Android recording completed: {path}")
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
                logger.debug(f"Already recording: {self.current_path}")
                return False
            
            self.recorder.start()
            self.recording = True
            logger.debug(f"Android recording started: {self.current_path}")
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
                logger.debug("Not recording Android audio, nothing to stop")
                return False
            
            self.recorder.stop()
            self.recorder.release()
            self.recorder = None
            self.recording = False
            logger.debug(f"Android recording stopped and saved: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Android recorder: {e}")
            self.recording = False
            return False
    
    def play(self, path: str) -> bool:
        """Play audio file using Android MediaPlayer"""
        try:
            self.stop()
            
            MediaPlayer = autoclass("android.media.MediaPlayer")
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(path)
            self.media_player.prepare()
            self.media_player.start()
            logger.debug(f"Started Android audio playback: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio on Android: {e}")
            return False
    
    def stop(self, log: bool = True) -> bool:
        """
        Stop any playing audio.
        If log is True, logs a debug message.
        Log param used to suppress log when stopping audio in on_leave.
        """
        try:
            if not self.media_player or not self.media_player.isPlaying():
                if log:
                    logger.debug("Android audio not playing, nothing to stop")
                return True

            self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            logger.debug(f"Stopped Android audio playback: {self.current_path}")
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

