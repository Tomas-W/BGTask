
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from src.utils.containers import BaseLayout, TopBarContainer, ScrollContainer
from src.utils.buttons import TopBar, TopBarButton

from src.settings import PATH

class SettingsScreen(Screen):
    def __init__(self, navigation_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar container
        self.top_bar_container = TopBarContainer()
        # Back button
        self.back_button = TopBarButton(img_path=PATH.BACK_IMG, side="left")
        self.back_button.bind(on_press=self.go_to_previous_screen)
        self.top_bar_container.add_widget(self.back_button)
        # Top bar
        self.top_bar = TopBar(text="Settings", button=False)
        self.top_bar_container.add_widget(self.top_bar)
        # Exit button
        self.exit_button = TopBarButton(img_path=PATH.EXIT_IMG, side="right")
        self.exit_button.bind(on_press=self.exit_app)
        self.top_bar_container.add_widget(self.exit_button)

        self.layout.add_widget(self.top_bar_container)

        # Settings container
        self.scroll_container = ScrollContainer()
        self.layout.add_widget(self.scroll_container)

        self.add_widget(self.root_layout)

    def go_to_previous_screen(self, instance):
        self.navigation_manager.go_back()

