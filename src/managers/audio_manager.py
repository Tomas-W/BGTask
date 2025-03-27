import os
import sys

from datetime import datetime
from plyer import audio

from kivy.utils import platform

from src.utils.android_recorder import AndroidAudioRecorder

from src.settings import PATH, PLATFORM, EXT


class AudioManager:
    """
    Manages audio accross the application.
    """
    def __init__(self):
        # Initialize the Android recorder
        self.android_recorder = AndroidAudioRecorder()
        self.alarm_storage_dir = self._get_alarm_storage()
        self.plyer_audio = audio
        self.plyer_audio.file_path = self.alarm_storage_dir

        # Alarms
        self.alarms = {}
        self.load_alarms()
        self.selected_alarm_name = None
        self.selected_alarm_path = None
        
        # Recording state
        self.is_recording = False
    
    def is_recording_granted(self):
        """Check if recording is granted"""
        if self.is_android():
            from android.permissions import check_permission, Permission  # type: ignore
            if not check_permission(Permission.RECORD_AUDIO):
                self.request_android_permissions()
                return False

        return True
    
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
        
            self.permissions_granted = True
    
    def _get_alarm_storage(self):
        """Get alarm storage path"""
        if platform == PLATFORM.ANDROID:
            from android.storage import app_storage_path  # type: ignore
            return os.path.join(app_storage_path(), PATH.ALARMS)
        else:
            return os.path.join(PATH.ALARMS)
    
    def get_recording_path(self):
        """Returns: filename, path, extension of a recording."""
        filename = f"recording_{datetime.now().strftime('%H-%M-%S')}"
        path = os.path.join(self.alarm_storage_dir, filename + EXT.WAV)
        return path, filename
    
    def load_alarms(self):
        """Load the alarm files from the storage path"""
        if os.path.isdir(self.alarm_storage_dir):
            alarms = {}
            for file in os.listdir(self.alarm_storage_dir):
                if file.endswith(EXT.WAV):
                    alarms[file.split(".")[0]] = os.path.join(self.alarm_storage_dir, file)
            self.alarms = alarms

        else:
            try:
                os.makedirs(self.alarm_storage_dir, exist_ok=True)
            except Exception as e:
                raise e
    
    def name_to_path(self, name):
        """Convert an alarm name to a path"""
        return os.path.join(self.alarm_storage_dir, f"{name}{EXT.WAV}")
    
    def path_to_name(self, path):
        """Convert a path to an alarm name"""
        return os.path.basename(path).split(".")[0]

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

    def start_recording(self):
        """Start recording audio using the appropriate method based on the platform"""
        if not self.is_recording_granted():
            return False
            
        path, filename = self.get_recording_path()
        
        try:
            if self.is_android():
                # Use AndroidAudioRecorder for Android
                if self.android_recorder.setup(path):
                    if self.android_recorder.start():
                        self.is_recording = True
                        self.selected_alarm_name = filename
                        self.selected_alarm_path = path
                        return True
                        
                # If Android recorder failed, try fallback to plyer
                self.plyer_audio.file_path = path
                
            # Use plyer for non-Android or as fallback
            self.plyer_audio.start()
            self.is_recording = True
            self.selected_alarm_name = filename
            self.selected_alarm_path = path
            return True
            
        except Exception as e:
            print(f"Recording error: {e}")
            return False
    
    def stop_recording(self):
        """Stop recording audio using the appropriate method based on the platform"""
        success = False
        try:
            if self.is_android() and self.android_recorder is not None:
                # Stop recording using AndroidAudioRecorder
                if self.android_recorder.stop():
                    success = True
            else:
                # Stop recording using plyer
                self.plyer_audio.stop()
                success = True
                
            if success and self.selected_alarm_path:
                # Read the recorded audio data
                with open(self.selected_alarm_path, "rb") as f:
                    audio_data = f.read()
                
                # Save the alarm
                self.load_alarms()
                
            self.is_recording = False
            return success
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
            self.is_recording = False
            return False
