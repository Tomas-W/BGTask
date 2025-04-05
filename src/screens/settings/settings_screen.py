from kivy.app import App

from src.screens.base.base_screen import BaseScreen

from src.widgets.containers import ScrollContainer


class SettingsScreen(BaseScreen):
    def __init__(self, navigation_manager, task_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager

        # TopBar title
        self.top_bar.bar_title.set_text("Settings")

        # Add bottom bar for scrolling to top
        self.add_bottom_bar()
        # Apply layout - already handled in BaseScreen
        self.add_widget(self.root_layout)
    
    def exit_app(self, instance) -> None:
        """Exit the application"""
        App.get_running_app().stop()
