from typing import TYPE_CHECKING

from src.screens.base.base_screen import BaseScreen

if TYPE_CHECKING:
    from src.managers.navigation_manager import NavigationManager
    from src.managers.app_task_manager import TaskManager
    from main import TaskApp


class SettingsScreen(BaseScreen):
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager

        # TopBar title
        self.top_bar.bar_title.set_text("Settings")

        # Add bottom bar for scrolling to top
        self.add_bottom_bar()
