import os
import sys

from plyer import audio
from kivy.utils import platform

from src.settings import PATH, PLATFORM, EXT


class AudioManager:
    """
    Manages audio accross the application.
    """
    def __init__(self):
        self.alarm_storage_path = self._get_alarm_storage()
        self.plyer_audio = audio
        self.plyer_audio.file_path = self.alarm_storage_path

        # Alarms
        self.alarms = {}
        self._load_alarms()
        self.selected_alarm_name = None
        self.selected_alarm_path = None
    
    def is_android(self):
        """Check if the app is running on Android"""
        return hasattr(sys, "getandroidapilevel")

    def request_android_permissions(self):
        """Request necessary Android permissions"""
        if self.is_android():
            try:
                from android.permissions import request_permissions, Permission  # type: ignore
                
                request_permissions([
                    Permission.RECORD_AUDIO,
                    Permission.WRITE_EXTERNAL_STORAGE, 
                    Permission.READ_EXTERNAL_STORAGE
                ])
            except Exception as e:
                raise e

    def _get_alarm_storage(self):
        """Get alarm storage path"""
        if platform == PLATFORM.ANDROID:
            from android.storage import app_storage_path  # type: ignore
            return os.path.join(app_storage_path(), PATH.ALARMS)
        else:
            return os.path.join(PATH.ALARMS)
    
    def _load_alarms(self):
        """Load the alarm files from the storage path"""
        if os.path.isdir(self.alarm_storage_path):
            alarms = {}
            for file in os.listdir(self.alarm_storage_path):
                if self.is_android():
                    if file.endswith((EXT.MP3, EXT.THREE_GP, EXT.WAV)):
                        print("*******************")
                        print(file)
                        print("*******************")
                        alarms[file.split(".")[0]] = os.path.join(self.alarm_storage_path, file)
                else:
                    if file.endswith((EXT.WAV, EXT.MP3)):
                        alarms[file.split(".")[0]] = os.path.join(self.alarm_storage_path, file)
            self.alarms = alarms
        else:
            try:
                os.makedirs(self.alarm_storage_path, exist_ok=True)
            except Exception as e:
                raise e
    
    def save_alarm(self, alarm_name, alarm_file):
        """Save alarm to alarm storage path"""
        if not alarm_name or not alarm_file:
            raise ValueError("Alarm name and file are required")
        
        # Create a unique filename
        filename = f"{alarm_name}"
        extension = EXT.WAV
        file_path = os.path.join(self.alarm_storage_path, filename + extension)
        if os.path.exists(file_path):
            filename += "_a"
            file_path = os.path.join(self.alarm_storage_path, filename + extension)
        # Save the alarm
        with open(file_path, "wb") as f:
            f.write(alarm_file)
        
        self._load_alarms()
    
    def name_to_path(self, name):
        """Convert an alarm name to a path"""
        return os.path.join(self.alarm_storage_path, f"{name}{EXT.WAV}")
    
    def path_to_name(self, path):
        """Convert a path to an alarm name"""
        return os.path.basename(path).split(".")[0]
    
    def get_extension(self, path):
        """Get the extension of the alarm"""
        return EXT.WAV
    
    def set_alarm_name(self, name=None, path=None):
        """Set the name of the alarm"""
        if path:
            self.selected_alarm_name = self.name_to_path(path)
        elif name:
            self.selected_alarm_name = name
        else:
            raise ValueError("Either name or path must be provided")
    
    def set_alarm_path(self, path=None, name=None):
        """Set the path of the alarm"""
        if path:
            self.selected_alarm_path = path
            self.selected_alarm_name = self.path_to_name(path)
        elif name:
            self.selected_alarm_path = self.name_to_path(name)
            self.selected_alarm_name = name
        else:
            raise ValueError("Either path or name must be provided")
