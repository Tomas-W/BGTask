from managers.audio.audio_manager import AudioManager
from service.service_device_manager import DM


class ServiceAudioManager(AudioManager):
    """
    Audio manager for the Service.
    No extra implementation to keep the same interface as AppAudioManager.
    """
    def __init__(self):
        super().__init__(is_service=True)
