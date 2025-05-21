from jnius import autoclass  # type: ignore

from src.utils.logger import logger


class AndroidAudioPlayer:
    """Android audio player for playback and vibration"""
    def __init__(self):
        self.audio_manager = None
        self.media_player = None
        self.vibrator = None
        self._java_classes = {}
        # Get service context if available
        try:
            PythonService = self._get_java_class("org.kivy.android.PythonService")
            self.service = PythonService.mService
        except:
            self.service = None

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

    def vibrate(self, duration: int = 1000) -> bool:
        """Vibrate the device for a specified duration."""
        try:
            if not self.vibrator:
                Context = self._get_java_class("android.content.Context")
                PythonActivity = self._get_java_class("org.kivy.android.PythonActivity")
                
                # Try service first (for background), fall back to activity
                if self.service:
                    self.vibrator = self.service.getSystemService(Context.VIBRATOR_SERVICE)
                elif PythonActivity.mActivity:
                    self.vibrator = PythonActivity.mActivity.getSystemService(Context.VIBRATOR_SERVICE)
                else:
                    logger.error("No Android context available for vibration")
                    return False
            
            if self.vibrator:
                self.vibrator.vibrate(duration)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error vibrating device: {e}")
            return False
    
    def stop_vibrator(self) -> bool:
        """Stop the vibrator and reset it."""
        try:
            if self.vibrator:
                self.vibrator.cancel()
                self.vibrator = None
            logger.trace("Vibration stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping vibration: {e}")
            return False