from kivy.core.audio import SoundLoader
from typing import Any

from src.utils.logger import logger


class WindowsAudioPlayer:
    """Manages audio playback for Windows devices."""
    def __init__(self):
        self.audio_manager: Any | None = None
        self.sound: Any | None = None

    def bind_audio_manager(self, audio_manager: Any | None) -> None:
        """Binds main AudioManager to the player."""
        self.audio_manager = audio_manager

    def play(self, path: str) -> bool:
        """
        Plays an audio file.
        Stops any playing audio before playing new one.
        """
        try:
            self.stop()
            
            sound = SoundLoader.load(path)
            if sound:
                sound.play()
                self.sound = sound
                logger.trace(f"Playing audio: {path}")
                return True
            
            else:
                logger.error(f"Error playing audio: could not load sound: {path}")
                return False
        
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def stop(self) -> bool:
        """Stops any playing audio."""
        try:
            if not self.sound or not self.sound.state == "play":
                return True
            
            self.sound.stop()
            self.sound = None
            return True
        
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
            return False
    
    def is_playing(self) -> bool:
        """Returns True if audio is currently playing."""
        try:
            return self.sound and self.sound.state == "play"
        
        except Exception as e:
            logger.error(f"Error checking is_playing status: {e}")
            return False

    def vibrate(self, *args, **kwargs) -> bool:
        """Stub implementation for Windows - vibration not supported"""
        return True
    
    def stop_vibrator(self, *args, **kwargs) -> bool:
        """Stub implementation for Windows - vibration not supported"""
        return True
