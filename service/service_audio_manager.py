from jnius import autoclass  # type: ignore

from service.service_logger import logger


class AudioPlayer:
    """Simple audio player for Android using MediaPlayer"""
    def __init__(self):
        self.media_player = None
        self._java_classes = {}
    
    def _get_java_class(self, class_name):
        """Lazy load Java classes"""
        if class_name not in self._java_classes:
            self._java_classes[class_name] = autoclass(class_name)
        return self._java_classes[class_name]
    
    def play(self, path):
        """Play an audio file"""
        try:
            self.stop()  # Stop any existing playback
            
            MediaPlayer = self._get_java_class("android.media.MediaPlayer")
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(path)
            self.media_player.prepare()
            self.media_player.start()
            logger.debug(f"AudioPlayer: Started playback: {path}")
            return True
            
        except Exception as e:
            logger.error(f"AudioPlayer: Error playing audio: {e}")
            return False
    
    def stop(self):
        """Stop audio playback"""
        try:
            if not self.media_player:
                return True
            
            if self.is_playing():
                self.media_player.stop()
            self.media_player.reset()
            self.media_player.release()
            self.media_player = None
            return True
            
        except Exception as e:
            logger.error(f"AudioPlayer: Error stopping playback: {e}")
            return False
    
    def is_playing(self):
        """Check if audio is currently playing"""
        try:
            return self.media_player and self.media_player.isPlaying()
        
        except Exception as e:
            logger.error(f"AudioPlayer: Error checking playback status: {e}")
            return False
