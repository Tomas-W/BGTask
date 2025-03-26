"""Android-specific audio support for Kivy"""
from kivy.utils import platform
from kivy.logger import Logger

def register_android_providers():
    """Register Android-specific audio providers"""
    # Only run this code on Android
    if platform != 'android':
        return
        
    try:
        # Import and register the Android media player
        from kivy.core.audio import SoundLoader
        from kivy.core.audio.audio_android import SoundAndroid
        
        # Check if already registered to avoid duplicate registration
        providers = SoundLoader.get_providers()
        if 'android' not in [p.__name__.lower() for p in providers]:
            Logger.info('Audio: Registering Android audio provider')
            SoundLoader.register(SoundAndroid)
            
    except Exception as e:
        Logger.error(f'Audio: Failed to register Android audio provider: {e}')

    # Log available providers for debugging
    try:
        from kivy.core.audio import SoundLoader
        Logger.info(f'Audio: Available providers: {[p.__name__ for p in SoundLoader.get_providers()]}')
    except Exception as e:
        Logger.error(f'Audio: Error getting providers: {e}')