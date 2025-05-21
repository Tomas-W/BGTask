from kivy.core.audio import SoundLoader

from src.utils.logger import logger


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
    
    def stop_vibrator(self, *args, **kwargs) -> bool:
        """Stub implementation for Windows - vibration not supported"""
        return True
