from managers.preferences.preferences_manager import PreferencesManager


class AppPreferencesManager(PreferencesManager):
    """
    Manages SharedPreferences for the app.
    """
    def __init__(self):
        super().__init__()
