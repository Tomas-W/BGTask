from jnius import autoclass  # type: ignore
from typing import Any

from src.utils.logger import logger


class AndroidAudioPlayer:
    """Manages audio playback and vibration for Android devices."""
    def __init__(self):
        self.audio_manager: Any | None = None
        self.media_player: Any | None = None
        self.vibrator: Any | None = None
        self._java_classes: dict[str, Any] = {}
        
        self.service: Any | None = self._get_service()
    
    def _get_service(self) -> Any | None:
        """Get the service context"""
        try:
            # Ran from Service
            PythonService = self._get_java_class("org.kivy.android.PythonService")
            return PythonService.mService
        except:
            # Ran from App
            return None

    def bind_audio_manager(self, audio_manager: Any | None) -> None:
        """Bind the main audio manager for state management"""
        self.audio_manager = audio_manager

    def _get_java_class(self, class_name: str) -> Any:
        """Lazy load Java classes"""
        if class_name not in self._java_classes:
            self._java_classes[class_name] = autoclass(class_name)
        return self._java_classes[class_name]

    def play(self, path: str) -> bool:
        """
        Play audio file.
        Stops any playing audio before playing new one.
        """
        try:
            self.stop()
            
            MediaPlayer = self._get_java_class("android.media.MediaPlayer")
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(path)
            self.media_player.prepare()
            self.media_player.start()
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

    def vibrate(self, duration: int = 1000) -> bool:
        """Vibrate the device for a specified duration."""
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
        """Get the vibrator"""
        Context = self._get_java_class("android.content.Context")
        PythonActivity = self._get_java_class("org.kivy.android.PythonActivity")
        try:
            if self.service:
                # Ran from Service
                return self.service.getSystemService(Context.VIBRATOR_SERVICE)
            elif PythonActivity.mActivity:
                # Ran from App
                return PythonActivity.mActivity.getSystemService(Context.VIBRATOR_SERVICE)
            else:
                logger.error("No Android context available for vibration")
                return None
        
        except Exception as e:
            logger.error(f"Error getting vibrator: {e}")
            return None
    
    def stop_vibrator(self) -> bool:
        """Stop the vibrator and reset it."""
        try:
            if self.vibrator:
                self.vibrator.cancel()
                self.vibrator = None
            return True
        
        except Exception as e:
            logger.error(f"Error stopping vibration: {e}")
            return False