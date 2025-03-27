class AndroidAudioRecorder:
    """Android-specific audio recording implementation"""

    def __init__(self):
        self.recorder = None
        
    def setup(self, path):
        """Configure the recorder for a new recording session"""
        try:
            from jnius import autoclass  # type: ignore
            MediaRecorder = autoclass("android.media.MediaRecorder")
            AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
            OutputFormat = autoclass("android.media.MediaRecorder$OutputFormat")
            AudioEncoder = autoclass("android.media.MediaRecorder$AudioEncoder")
            
            self.recorder = MediaRecorder()
            self.recorder.setAudioSource(AudioSource.MIC)
            
            # no direct support for .wav
            # use 3GP instead
            self.recorder.setOutputFormat(OutputFormat.THREE_GPP)
            self.recorder.setAudioEncoder(AudioEncoder.AMR_NB)
            
            self.recorder.setOutputFile(path)
            self.recorder.prepare()
            return True
        except Exception as e:
            print(f"Error setting up recorder: {e}")
            return False

    def start(self):
        """Start the recording"""
        try:
            if self.recorder:
                self.recorder.start()
                return True
            return False
        except Exception as e:
            print(f"Error starting recorder: {e}")
            return False

    def stop(self):
        """Stop the recording and release resources"""
        try:
            if self.recorder:
                self.recorder.stop()
                self.recorder.release()
                self.recorder = None
                return True
            return False
        except Exception as e:
            print(f"Error stopping recorder: {e}")
            return False
            
    def release(self):
        """Release resources without stopping (for cleanup)"""
        try:
            if self.recorder:
                self.recorder.release()
                self.recorder = None
        except Exception as e:
            print(f"Error releasing recorder: {e}")