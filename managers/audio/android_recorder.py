from jnius import autoclass  # type: ignore
from typing import Any

from src.utils.logger import logger


class AndroidAudioRecorder:
    """Manages audio recording for Android devices."""
    # Java classes
    MEDIA_RECORDER = "android.media.MediaRecorder"
    AUDIO_SOURCE = "android.media.MediaRecorder$AudioSource"
    OUTPUT_FORMAT = "android.media.MediaRecorder$OutputFormat"
    AUDIO_ENCODER = "android.media.MediaRecorder$AudioEncoder"

    def __init__(self):
        self.recorder: Any | None = None
        self.recording: bool = False
        self.current_path: str | None = None
        self._java_classes: dict[str, Any] = {}

    def _get_java_class(self, class_name: str) -> Any:
        """Lazy load Java classes."""
        if class_name not in self._java_classes:
            self._java_classes[class_name] = autoclass(class_name)
        
        return self._java_classes[class_name]

    def setup_recording(self, path: str) -> bool:
        """Configures the recorder for a new recording session."""
        try:
            MediaRecorder = self._get_java_class(AndroidAudioRecorder.MEDIA_RECORDER)
            AudioSource = self._get_java_class(AndroidAudioRecorder.AUDIO_SOURCE)
            OutputFormat = self._get_java_class(AndroidAudioRecorder.OUTPUT_FORMAT)
            AudioEncoder = self._get_java_class(AndroidAudioRecorder.AUDIO_ENCODER)
            
            # Reset existing recorder
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
            logger.error(f"Error setting up recorder: {e}")
            return False

    def start_recording(self) -> bool:
        """Starts recording audio."""
        try:
            if self.recording:
                logger.error(f"Already recording: {self.current_path}")
                return False
            
            if not self.recorder:
                logger.error("Error starting recording - recorder not found")
                return False
            
            self.recorder.start()
            self.recording = True
            logger.trace(f"Started recording: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting recorder: {e}")
            return False

    def stop_recording(self) -> bool:
        """Stops the recording and releases resources."""
        try:
            if not self.recording:
                logger.error("Error stopping recording - not recording")
                return False
            
            if not self.recorder:
                logger.error("Error stopping recording - recorder not found")
                return False

            self.recorder.stop()
            self.recorder.release()
            self.recorder = None
            self.recording = False
            logger.trace(f"Stopped and saved recording: {self.current_path}")
            return True
        
        except Exception as e:
            self.recording = False
            logger.error(f"Error stopping recorder: {e}")
            return False

    def release(self) -> bool:
        """Releases recorder resources without stopping (for cleanup)."""
        try:
            if self.recorder:
                self.recorder.release()
                self.recorder = None
            
            self.recording = False
            return True
        
        except Exception as e:
            logger.error(f"Error releasing recorder resources: {e}")
            return False
