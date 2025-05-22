import pyaudio
import wave

from typing import Any

from src.utils.logger import logger


class WindowsAudioRecorder:
    """Manages audio recording for Windows devices."""
    def __init__(self):
        self.current_path: str | None = None
        self.recording: bool = False
        self.stream: Any | None = None
        self.frames: list[bytes] = []
        self.pa: Any | None = None
        
        try:            
            self.pyaudio = pyaudio
            self.wave = wave
            self.pa = pyaudio.PyAudio()
        
        except Exception as e:
            logger.error(f"Error initializing PyAudio: {e}")

    def setup_recording(self, path: str) -> bool:
        """Configure the recorder for a new recording session."""
        try:
            self.current_path = path
            self.frames = []
            return True
        
        except Exception as e:
            logger.error(f"Error setting up recorder: {e}")
            return False
    
    def start_recording(self) -> bool:
        """Start recording audio."""
        try:
            if self.recording:
                logger.error(f"Already recording: {self.current_path}")
                return False
            
            self.recording = True
            self.frames = []

            def callback(in_data: bytes, frame_count: int,
                         time_info: Any, status: Any) -> tuple[bytes, int]:
                if self.recording:
                    self.frames.append(in_data)
                    return (in_data, self.pyaudio.paContinue)
                
                return (in_data, self.pyaudio.paComplete)
            
            # Open stream using callback
            self.stream = self.pa.open(
                format=self.pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024,
                stream_callback=callback
            )
            
            self.stream.start_stream()
            logger.trace(f"Recording started: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.recording = False
            return False
    
    def stop_recording(self) -> bool:
        try:
            if not self.recording:
                logger.error("Not recording, nothing to stop.")
                return False
            
            self.recording = False
            
            # Stop and close stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                logger.trace("Recording stopped.")
            
            # Save recording to WAV file
            if self.frames and self.current_path:
                wf = self.wave.open(self.current_path, "wb")
                wf.setnchannels(1)
                wf.setsampwidth(self.pa.get_sample_size(self.pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b"".join(self.frames))
                wf.close()
                logger.trace(f"Recording stopped and saved: {self.current_path}")
                return True
            
            else:
                logger.error("No data recorded.")
                return False
        
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False

    def release(self) -> bool:
        """Release recorder resources without stopping (for cleanup)."""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                
            if self.pa:
                self.pa.terminate()
                self.pa = None
                
            self.recording = False
            return True
        
        except Exception as e:
            logger.error(f"Error releasing recorder resources: {e}")
            return False
