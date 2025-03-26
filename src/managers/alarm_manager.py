import sys
import os
from plyer import audio

def is_android():
    """Check if the app is running on Android"""
    return hasattr(sys, "getandroidapilevel")

class AlarmManager:
    def __init__(self):
        # Initialize basic properties
        self.selected_alarm_name = None
        self.selected_alarm_path = None
        
        # Initialize Plyer audio
        self.plyer_audio = audio
        
        # Store available alarms
        # Code to load your available alarms would go here
        
        # We won't initialize Android-specific components here
        # since they should be created fresh for each recording session
        
        # Configure for Android if needed
        if is_android():
            try:
                # Pre-configure with more compatible settings
                from jnius import autoclass
                MediaRecorder = autoclass('android.media.MediaRecorder')
                AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
                OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
                AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
                
                # We won't create the recorder here, but we'll set these classes for later use
                self.MediaRecorder = MediaRecorder
                self.AudioSource = AudioSource
                self.OutputFormat = OutputFormat
                self.AudioEncoder = AudioEncoder
                
                # Configure plyer's android audio module if possible
                if hasattr(self.plyer_audio, '_recorder'):
                    # If recorder already exists, release it
                    try:
                        self.plyer_audio._recorder.release()
                    except:
                        pass
                    
                # Create a new recorder with more compatible settings
                self.plyer_audio._recorder = MediaRecorder()
            except Exception as e:
                print(f"Error configuring MediaRecorder: {e}")
        
        # ... rest of your initialization ... 