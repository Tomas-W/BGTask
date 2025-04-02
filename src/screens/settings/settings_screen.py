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

        # Scroll container
        self.scroll_container = ScrollContainer()

        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)
    
    def exit_app(self, instance) -> None:
        """Exit the application"""
        App.get_running_app().stop()
