import os

from plyer import audio
from kivy.utils import platform

from src.settings import PATH


class AlarmManager:
    """
    Manages alarms and their storage.
    """
    def __init__(self):
        self.storage_path = self._get_storage_path()
        self.alarms = {}
        self.load_alarms()

        self.plyer_audio = audio
        self.plyer_audio.file_path = self.storage_path


        self.selected_alarm_name = None
        self.selected_alarm_path = None

    def _get_storage_path(self):
        """Get the storage path based on platform"""
        if platform == "android":
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), PATH.ALARMS)
        else:
            return os.path.join(PATH.ALARMS)
    
    def load_alarms(self):
        """Load the alarms from the storage path"""
        if os.path.isdir(self.storage_path):
            alarms = {}
            for file in os.listdir(self.storage_path):
                # Support both .wav and .3gp extensions
                if file.endswith((".wav", ".3gp")):
                    alarms[file.split(".")[0]] = os.path.join(self.storage_path, file)
            self.alarms = alarms
            print(self.alarms)
        else:
            # Create the directory instead of raising an error
            try:
                os.makedirs(self.storage_path, exist_ok=True)
                print(f"Created alarm directory at {self.storage_path}")
            except Exception as e:
                print(f"Error creating alarm directory: {e}")
    
    def save_alarm(self, alarm_name, alarm_file):
        """Save an alarm to the storage path"""
        if not alarm_name or not alarm_file:
            raise ValueError("Alarm name and file are required")
        
        # Create a unique filename
        filename = f"{alarm_name}"
        extension = ".wav"
        file_path = os.path.join(self.storage_path, filename)
        if os.path.exists(file_path):
            filename += "_a"
            file_path = os.path.join(self.storage_path, filename)
        # Save the alarm file
        with open(file_path, "wb") as f:
            f.write(alarm_file)
        
        self.load_alarms()
