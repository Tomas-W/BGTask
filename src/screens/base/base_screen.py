from typing import Callable

from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from src.widgets.bars import TopBarClosed, TopBarExpanded, BottomBar
from src.widgets.containers import BaseLayout

from src.settings import SCREEN


class BaseScreen(Screen):
    """Base screen class that implements common functionality for all screens."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.top_bar_is_expanded = False

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        self.top_bar = TopBarClosed(
            top_left_callback=lambda instance: self.navigation_manager.go_back(),
            options_callback=lambda instance: self.switch_top_bar(),
        )
        self.top_bar_expanded = TopBarExpanded(
            top_left_callback=lambda instance: self.navigation_manager.go_back(),
            screenshot_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.START),
            options_callback=lambda instance: self.switch_top_bar(),
            settings_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.SETTINGS),
            exit_callback=lambda instance: self.navigation_manager.exit_app(),
        )

        self.layout.add_widget(self.top_bar.top_bar_container)
    
    def add_bottom_bar(self):
        """Add a bottom bar to the screen to scroll to the top"""
        # Bottom bar with ^ button
        self.bottom_bar = BottomBar(text="^")
        self.bottom_bar.bind(on_release=self.scroll_container.scroll_to_top)
        self.scroll_container.connect_bottom_bar(self.bottom_bar)
        self.root_layout.add_widget(self.bottom_bar)

    def switch_top_bar(self, on_enter: bool = False, *args) -> None:
        """
        Controls the state of the TopBar:
        - Base bar [ Edit/Back | TopBar | Options ]
        - Expanded bar [ Edit/Back | TopBar | Screenshot | Settings | Exit | Options ]
        """
        # Toggle state
        if not on_enter:
            self.top_bar_is_expanded = not self.top_bar_is_expanded
        
        # Switch the top bar
        if self.top_bar_is_expanded and self.top_bar.top_bar_container in self.layout.children:
            self.layout.remove_widget(self.top_bar.top_bar_container)
            self.layout.add_widget(self.top_bar_expanded.top_bar_container, index=len(self.layout.children))
        elif not self.top_bar_is_expanded and self.top_bar_expanded.top_bar_container in self.layout.children:
            self.layout.remove_widget(self.top_bar_expanded.top_bar_container)
            self.layout.add_widget(self.top_bar.top_bar_container, index=len(self.layout.children))
    
    def set_callback(self, callback: Callable) -> None:
        """Set the callback function to be called."""
        self.callback = callback
    
    def set_button_state(self, button, active=True, enabled=True, text=None):
        """
        Set a button's state.
        - active: Whether the button should be active
        - enabled: Whether the button should be enabled
        - text: Optional new text for the button
        """
        if text:
            button.set_text(text)
        
        if active:
            button.set_active_state()
        else:
            button.set_inactive_state()
            
        button.set_disabled(not enabled)
    
    def show_error_popup(self, title, message):
        """
        Show an error popup with the given title and message.
        """
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()

    def on_pre_enter(self) -> None:
        """Called before the screen is entered."""
        self.top_bar_is_expanded = False
        self.switch_top_bar(on_enter=True)
    
    def on_enter(self) -> None:
        """Called when the screen is entered."""
        pass    
