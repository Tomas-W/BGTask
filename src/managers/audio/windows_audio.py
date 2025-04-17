try:
    import pyaudio
    import wave
except ImportError:
    pass

from kivy.core.audio import SoundLoader

from src.utils.logger import logger


class WindowsAudioPlayer:
    """Windows-specific audio implementation for recording and playback."""
    def __init__(self):
        self.audio_manager = None

        self.current_path: str | None = None
        self.recording: bool = False
        self.stream = None
        self.frames: list[bytes] = []
        self.pa = None
        self.sound = None
        
        try:            
            self.pyaudio = pyaudio
            self.wave = wave
            self.pa = pyaudio.PyAudio()
        
        except Exception as e:
            logger.error(f"Error initializing PyAudio: {e}")
    
    def bind_audio_manager(self, audio_manager):
        self.audio_manager = audio_manager
    
    def setup_recording(self, path: str) -> bool:
        """Configure the recorder for a new recording session."""        
        try:
            self.current_path = path
            self.frames = []
            return True
        
        except Exception as e:
            logger.error(f"Error setting up Windows recorder: {e}")
            return False
    
    def start_recording(self) -> bool:       
        try:
            if self.recording:
                logger.error(f"Already recording: {self.current_path}")
                return False
            
            self.recording = True
            self.frames = []

            def callback(in_data, frame_count, time_info, status):
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
            logger.debug(f"Windows recording started: {self.current_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting Windows recording: {e}")
            self.recording = False
            return False
    
    def stop_recording(self) -> bool:
        try:
            if not self.recording:
                logger.error("Not recording Windows audio, nothing to stop")
                return False
            
            self.recording = False
            
            # Stop and close stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                logger.debug("Windows recording stopped")
            
            # Save recording to WAV file
            if self.frames and self.current_path:
                wf = self.wave.open(self.current_path, "wb")
                wf.setnchannels(1)
                wf.setsampwidth(self.pa.get_sample_size(self.pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b"".join(self.frames))
                wf.close()
                return True
            
            else:
                logger.error("No Windows audio data recorded")
                return False
        
        except Exception as e:
            logger.error(f"Error stopping Windows recording: {e}")
            return False
    
    def play(self, path: str) -> bool:
        """Play audio file using Kivy SoundLoader"""
        try:
            self.stop()
            
            sound = SoundLoader.load(path)
            if sound:
                sound.play()
                self.sound = sound
                logger.debug(f"Started Windows audio playback: {path}")
                return True
            
            else:
                logger.error(f"Could not load sound: {path}")
                return False
        
        except Exception as e:
            logger.error(f"Error playing audio on Windows: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop any playing audio.
        If log is True, logs a debug message.
        Log param used to suppress log when stopping audio in on_leave.
        """
        try:
            if not self.sound or not self.sound.state == "play":
                return True
            
            self.sound.stop()
            self.sound = None
            logger.debug("Stopped Windows audio playback")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping audio on Windows: {e}")
            return False
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        try:
            return self.sound and self.sound.state == "play"
        
        except Exception as e:
            logger.error(f"Error checking playback status on Windows: {e}")
            return False
    
    def release(self) -> bool:
        """Release any resources"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                
            if self.pa:
                self.pa.terminate()
                self.pa = None
                
            self.recording = False
            self.stop()
            return True
        
        except Exception as e:
            logger.error(f"Error releasing Windows audio resources: {e}")
            return False
    
    def vibrate(self, *args, **kwargs) -> bool:
        """Stub implementation for Windows - vibration not supported"""
        return True
