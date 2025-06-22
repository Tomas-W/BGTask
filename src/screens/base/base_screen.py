from typing import Callable

from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle

from src.widgets.bars import TopBarClosed, TopBarExpanded
from src.widgets.containers import BaseLayout, ScrollContainer

from managers.device.device_manager import DM
from src.settings import STATE


from kivy.uix.label import Label
from kivy.clock import Clock
from collections import deque
from src.settings import COL, FONT, SIZE


class FPSCounter(Label):
    """
    FPS counter using Kivy's built-in FPS tracking.
    """
    def __init__(self, **kwargs):
        super().__init__(
            text="FPS: 0",
            size_hint=(1, None),
            height=SIZE.HEADER_HEIGHT,
            halign="right",
            valign="middle",
            font_size=FONT.DEFAULT,
            color=COL.TEXT_GREY,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))

        with self.canvas.before:
            self.bg_color = Color(*COL.BG)
            self.bg_rect = Rectangle(
                pos=self.pos,
                size=self.size
            )
            self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Update FPS display every 0.5 seconds
        Clock.schedule_interval(self.update_fps, 0.5)
    
    def _update_bg(self, instance, value: float) -> None:
        """Updates the background size of the TaskContainer."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def update_fps(self, dt):
        """Updates the FPS display using Kivy's built-in FPS."""
        fps = Clock.get_fps()
        self.text = f"FPS: {fps:.1f}"


class BaseScreen(Screen):
    """
    Base screen class that implements common functionality for all screens.
    - TopBar / TopBarExpanded
    - ScrollContainer [ ScrollView with main content ]
    - BottomBar with spacer animation
    - Button state functionality
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)        

        self.top_bar_is_expanded = False
        
        self.root_layout = RelativeLayout()
        
        # Main content container
        self.layout = BaseLayout()

        self.top_bar = TopBarClosed(
            top_left_callback=lambda instance: self.navigation_manager.go_back(),
            options_callback=lambda instance: self.switch_top_bar(),
        )
        self.top_bar_expanded = TopBarExpanded(
            top_left_callback=lambda instance: self.navigation_manager.go_back(),
            screenshot_callback=self._screenshot_callback,
            options_callback=lambda instance: self.switch_top_bar(),
            settings_callback=lambda instance: self.navigation_manager.navigate_to(DM.SCREEN.SETTINGS),
            exit_callback=lambda instance: self.navigation_manager.exit_app(),
        )
        self.layout.add_widget(self.top_bar.top_bar_container)
        
        # ScrollContainer
        self.scroll_container = ScrollContainer(
            parent_screen=self,
            allow_scroll_y=True,
            allow_scroll_x=False
        )
        # FPS Counter
        self.fps_counter = FPSCounter()
        self.layout.add_widget(self.fps_counter)

        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

    def _screenshot_callback(self, instance):
        """
        Screenshot the screen.
        """
        self.navigation_manager.navigate_to(DM.SCREEN.WALLPAPER)

    def switch_top_bar(self, on_enter: bool = False, *args) -> None:
        """
        Switches between:
        - TopBar [ Edit/Back | TopBar | Options ]
        - TopBarExpanded [ Edit/Back | TopBar | Screenshot | Settings | Exit | Options ]
        on_enter: True if called from on_enter to not change state.
        """
        # Toggle state
        if not on_enter:
            self.top_bar_is_expanded = not self.top_bar_is_expanded
        
        # Make TopBarExpanded
        if self.top_bar_is_expanded and self.top_bar.top_bar_container in self.layout.children:
            self.layout.remove_widget(self.top_bar.top_bar_container)
            self.layout.add_widget(self.top_bar_expanded.top_bar_container, index=len(self.layout.children))
        
        # Make TopBar
        elif not self.top_bar_is_expanded and self.top_bar_expanded.top_bar_container in self.layout.children:
            self.layout.remove_widget(self.top_bar_expanded.top_bar_container)
            self.layout.add_widget(self.top_bar.top_bar_container, index=len(self.layout.children))
    
    def set_callback(self, callback: Callable) -> None:
        """Set callback function to be called."""
        self.callback = callback
    
    def on_pre_enter(self) -> None:
        """Called before the screen is entered."""
        # Make TopBar
        self.top_bar_is_expanded = False
        self.switch_top_bar(on_enter=True)
    
    def on_enter(self) -> None:
        """Called when the screen is entered."""
        pass
    
    def set_button_state(self, button, active=True, enabled=True, text=None):
        """
        Set a Button's state.
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