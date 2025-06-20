from typing import TYPE_CHECKING

from managers.preferences.preferences_manager import PreferencesManager

if TYPE_CHECKING:
    from main import TaskApp


class AppPreferencesManager(PreferencesManager):
    """
    Manages SharedPreferences for the app.
    """
    def __init__(self, app: "TaskApp"):
        super().__init__()
        self.app = app
