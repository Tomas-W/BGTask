from jnius import autoclass  # type: ignore
from typing import Any

from src.utils.logger import logger


class AndroidAudioPlayer:
    VIBRATION_DURATION = 1000  # milliseconds
    # Java classes
    MEDIA_PLAYER = "android.media.MediaPlayer"
    CONTEXT = "android.content.Context"
    PYTHON_ACTIVITY = "org.kivy.android.PythonActivity"
    PYTHON_SERVICE = "org.kivy.android.PythonService"

    """Manages audio playback and vibration for Android devices."""
    def __init__(self):
        self.audio_manager: Any | None = None
        self.media_player: Any | None = None
        self.vibrator: Any | None = None
        self._java_classes: dict[str, Any] = {}
        
        self.service: Any | None = self._get_service()
    
    def _get_service(self) -> Any | None:
        """Gets the service context."""
        try:
            # Ran from Service
            PythonService = self._get_java_class(AndroidAudioPlayer.PYTHON_SERVICE)
            return PythonService.mService
        
        except:
            # Ran from App
            return None

    def bind_audio_manager(self, audio_manager: Any | None) -> None:
        """Binds main AudioManager to the player."""
        self.audio_manager = audio_manager

    def _get_java_class(self, class_name: str) -> Any:
        """Lazy load Java classes."""
        if class_name not in self._java_classes:
            self._java_classes[class_name] = autoclass(class_name)
        
        return self._java_classes[class_name]

    def play(self, path: str) -> bool:
        """
        Plays an audio file.
        Stops any playing audio before playing new one.
        """
        try:
            self.stop()
            
            MediaPlayer = self._get_java_class(AndroidAudioPlayer.MEDIA_PLAYER)
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(path)
            self.media_player.prepare()
            self.media_player.start()
            logger.trace(f"Playing audio: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False

    def stop(self) -> bool:
        """Stop any playing audio."""
        try:
            if not self.media_player or not self.media_player.isPlaying():
                return True

            self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            return True
        
        except Exception as e:
            logger.error(f"Error stopping audio playback: {e}")
            return False

    def is_playing(self) -> bool:
        """Returns True if audio is currently playing."""
        try:
            return self.media_player and self.media_player.isPlaying()
        
        except Exception as e:
            logger.error(f"Error checking is_playing status: {e}")
            return False

    def vibrate(self, duration: int = VIBRATION_DURATION) -> bool:
        """Vibrates the device for a specified duration."""
        try:
            if not self.vibrator:
                self.vibrator = self._get_vibrator()
            
            if self.vibrator:
                self.vibrator.vibrate(duration)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error vibrating device: {e}")
            return False
    
    def _get_vibrator(self) -> Any | None:
        """Gets the vibrator service."""
        Context = self._get_java_class(AndroidAudioPlayer.CONTEXT)
        PythonActivity = self._get_java_class(AndroidAudioPlayer.PYTHON_ACTIVITY)
        try:
            if self.service:
                # Ran from Service
                return self.service.getSystemService(Context.VIBRATOR_SERVICE)
            elif PythonActivity.mActivity:
                # Ran from App
                return PythonActivity.mActivity.getSystemService(Context.VIBRATOR_SERVICE)
            else:
                logger.error("Error getting vibrator - no context available")
                return None
        
        except Exception as e:
            logger.error(f"Error getting vibrator: {e}")
            return None
    
    def stop_vibrator(self) -> bool:
        """Stops the vibrator and resets it."""
        try:
            if self.vibrator:
                self.vibrator.cancel()
                self.vibrator = None
            return True
        
        except Exception as e:
            logger.error(f"Error stopping vibration: {e}")
            return False
