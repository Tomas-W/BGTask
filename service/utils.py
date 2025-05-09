import os

from jnius import autoclass  # type: ignore


NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
AndroidNotificationManager = autoclass("android.app.NotificationManager")


def get_storage_path(path):
        """Returns the storage path"""
        app_dir = os.environ.get("ANDROID_PRIVATE", "")
        return os.path.join(app_dir, path)


class Paths:
    """Constants for paths"""
    TASK_FILE = get_storage_path("app/src/assets/first_task.json")

    SERVICE_FLAG = get_storage_path("app/service/service_stop.flag")
    SNOOZE_A_FLAG = get_storage_path("app/service/snooze_a.flag")
    SNOOZE_B_FLAG = get_storage_path("app/service/snooze_b.flag")
    STOP_FLAG = get_storage_path("app/service/stop.flag")

    AUDIO_TASK_EXPIRED = get_storage_path("app/src/assets/alarms/rooster.wav")


class NotificationChannels:
    """Constants for notification channels"""
    FOREGROUND = "foreground_channel"
    TASKS = "tasks_channel"

class NotificationPriority:
    """Constants for notification priorities"""
    LOW = NotificationCompat.PRIORITY_LOW
    DEFAULT = NotificationCompat.PRIORITY_DEFAULT
    HIGH = NotificationCompat.PRIORITY_HIGH

class NotificationImportance:
    """Constants for notification channel importance"""
    LOW = AndroidNotificationManager.IMPORTANCE_LOW
    DEFAULT = AndroidNotificationManager.IMPORTANCE_DEFAULT
    HIGH = AndroidNotificationManager.IMPORTANCE_HIGH

class NotificationActions:
    """Constants for notification actions"""
    OPEN_APP = "open_app"
    SNOOZE_A = "snooze_a"
    SNOOZE_B = "snooze_b"
    STOP = "stop"


class PendingIntents:
    """Constants for pending intents"""
    OPEN_APP = 11
    SNOOZE_A = 12
    SNOOZE_B = 13
    STOP = 14


PATH = Paths()
CHANNEL = NotificationChannels()
PRIORITY = NotificationPriority()
IMPORTANCE = NotificationImportance()
ACTION = NotificationActions()
INTENT = PendingIntents()


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
            print(f"AudioPlayer: Started playback: {path}")
            return True
            
        except Exception as e:
            print(f"AudioPlayer: Error playing audio: {e}")
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
            print(f"AudioPlayer: Error stopping playback: {e}")
            return False
    
    def is_playing(self):
        """Check if audio is currently playing"""
        try:
            return self.media_player and self.media_player.isPlaying()
        except Exception as e:
            print(f"AudioPlayer: Error checking playback status: {e}")
            return False
