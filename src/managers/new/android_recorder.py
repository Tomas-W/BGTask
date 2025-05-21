from jnius import autoclass  # type: ignore

from src.utils.logger import logger


class AndroidAudioRecorder:
    """Android audio recorder for capturing audio"""
    def __init__(self):
        self.recorder = None
        self.recording = False
        self.current_path = None
        self._java_classes = {}

    def _get_java_class(self, class_name: str):
        """Lazy load Java classes only when needed"""
        if class_name not in self._java_classes:
            self._java_classes[class_name] = autoclass(class_name)
        return self._java_classes[class_name]

    def setup_recording(self, path: str) -> bool:
        """Configure the recorder for a new recording session"""
        try:
            # Lazy load Java classes only when needed
            MediaRecorder = self._get_java_class("android.media.MediaRecorder")
            AudioSource = self._get_java_class("android.media.MediaRecorder$AudioSource")
            OutputFormat = self._get_java_class("android.media.MediaRecorder$OutputFormat")
            AudioEncoder = self._get_java_class("android.media.MediaRecorder$AudioEncoder")
            
            # Reset any existing recorder
            if self.recorder:
                self.recorder.release()
            
            self.recorder = MediaRecorder()
            self.recorder.setAudioSource(AudioSource.MIC)
            
            # no direct support for .wav
            # use 3GP instead
            self.recorder.setOutputFormat(OutputFormat.THREE_GPP)
            self.recorder.setAudioEncoder(AudioEncoder.AMR_NB)
            
            self.recorder.setOutputFile(path)
            self.recorder.prepare()
            self.current_path = path
            return True
        
        except Exception as e:
            logger.error(f"Error setting up Android recorder: {e}")
            return False

    def start_recording(self) -> bool:
        """Start recording audio"""
        try:
            if not self.recorder:
                logger.error("Android recorder not found, setup recording first")
                return False
                
            if self.recording:
                logger.error(f"Already recording: {self.current_path}")
                return False
            
            self.recorder.start()
            self.recording = True
            logger.trace(f"Android recording started: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting Android recorder: {e}")
            return False

    def stop_recording(self) -> bool:
        """Stop the recording and release resources"""
        try:
            if not self.recorder:
                logger.error("Android recorder not set-up")
                return False
                
            if not self.recording:
                logger.error("Not recording Android audio, nothing to stop")
                return False
            
            self.recorder.stop()
            self.recorder.release()
            self.recorder = None
            self.recording = False
            logger.trace(f"Android recording stopped and saved: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Android recorder: {e}")
            self.recording = False
            return False

    def release(self) -> bool:
        """Release recorder resources without stopping (for cleanup)"""
        try:
            if self.recorder:
                self.recorder.release()
                self.recorder = None
            
            self.recording = False
            return True
        
        except Exception as e:
            logger.error(f"Error releasing Android recorder resources: {e}")
            return False
