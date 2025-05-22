from src.managers.new_audio_manager import AudioManager


class ServiceAudioManager(AudioManager):
    """Audio manager for the service"""
    def __init__(self):
        super().__init__(is_service=True)
