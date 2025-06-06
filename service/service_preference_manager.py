from typing import Any

from managers.preferences.preferences_manager import PreferencesManager


class ServicePreferencesManager(PreferencesManager):
    """
    Manages SharedPreferences for the service.
    """
    def __init__(self, service_context: Any):
        super().__init__(service_context)
