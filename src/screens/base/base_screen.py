from typing import Callable

from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.animation import Animation, AnimationTransition

from src.widgets.bars import TopBarClosed, TopBarExpanded, BottomBar
from src.widgets.containers import BaseLayout, ScrollContainer
from src.widgets.misc import Spacer

from src.settings import SCREEN, SIZE, COL


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
        
        # Setup scroll container
        self.setup_scroll_container()
        
        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        
        # Attributes for bottom bar and spacer animation
        self.animating_spacer = False
        self.initial_scroll = True
        self.initial_scroll_timer_set = False
    
    def setup_scroll_container(self, allow_scroll_y=True, allow_scroll_x=True):
        """
        Set up the scroll container for this screen.
        
        Args:
            allow_scroll_y (bool): Whether vertical scrolling is allowed
            allow_scroll_x (bool): Whether horizontal scrolling is allowed
        """
        self.scroll_container = ScrollContainer(
            scroll_callback=self.check_for_bottom_spacer,
            allow_scroll_y=allow_scroll_y,
            allow_scroll_x=allow_scroll_x
        )
        self.scroll_container.main_self = self
    
    def add_bottom_bar(self):
        """Add a bottom bar to the screen to scroll to the top"""
        # Bottom bar with ^ button
        self.bottom_bar = BottomBar(text="^")
        self.bottom_bar.bind(on_release=self.scroll_container.scroll_to_top)
        self.scroll_container.connect_bottom_bar(self.bottom_bar)
        # Add a reference to parent screen for synchronized animations
        self.bottom_bar.parent_screen = self
        self.root_layout.add_widget(self.bottom_bar)
        
        # Initialize the spacer with 0 height
        self.bottom_spacer = Spacer(height=0, color=COL.BG)
        self.layout.add_widget(self.bottom_spacer)
        
        # Ensure bottom bar is fully hidden initially
        self.bottom_bar.opacity = 0
        self.bottom_bar.visible = False
        self.bottom_bar.pos_hint = {"center_x": 0.5, "y": -0.15}
    
    def synchronized_animate(self, show_bottom_bar):
        """
        Synchronize the bottom bar and spacer animations perfectly.
        Both animations will start at the exact same moment with identical parameters.
        
        Args:
            show_bottom_bar (bool): Whether to show or hide the bottom bar and adjust spacer
        """
        # Mark animations as in progress
        self.animating_spacer = True
        
        # Set bottom bar visibility state first (before animation starts)
        self.bottom_bar.visible = show_bottom_bar
        
        # Use the same animation parameters for both elements
        duration = 0.3
        
        # Create animations
        if show_bottom_bar:
            # Show animations
            bar_anim = Animation(
                opacity=1, 
                pos_hint={"center_x": 0.5, "y": 0}, 
                duration=duration,
                transition=AnimationTransition.out_quad
            )
            
            spacer_anim = Animation(
                height=SIZE.BOTTOM_BAR_HEIGHT*1.05, 
                duration=0.3,
                transition=AnimationTransition.in_quad
            )
        else:
            # Hide animations
            bar_anim = Animation(
                opacity=0, 
                pos_hint={"center_x": 0.5, "y": -0.15}, 
                duration=duration,
                transition=AnimationTransition.in_quad
            )
            
            spacer_anim = Animation(
                height=0, 
                duration=0.3,
                transition=AnimationTransition.out_quad
            )
        
        # Bind completion to reset animation flag
        spacer_anim.bind(on_complete=lambda *args: setattr(self, "animating_spacer", False))
        
        # Start both animations simultaneously
        bar_anim.start(self.bottom_bar)
        spacer_anim.start(self.bottom_spacer)
    
    def reset_bottom_bar_state(self):
        """
        Reset bottom bar to a clean hidden state without animation.
        Used when entering the screen to ensure proper initial state.
        """
        # Immediately set properties without animation
        self.bottom_bar.opacity = 0
        self.bottom_bar.pos_hint = {"center_x": 0.5, "y": -0.15}
        self.bottom_bar.visible = False
        self.bottom_spacer.height = 0
        self.animating_spacer = False
        
        # Reset scroll container's tracking too
        self.scroll_container.last_pixels_scrolled = 0
    
    def check_for_bottom_spacer(self, *args) -> None:
        """
        Synchronize spacer animation with bottom bar animation.
        This is called when the scroll position changes or when bar visibility state changes.
        """
        # During initial scroll setup, don't process animations
        if hasattr(self, "initial_scroll") and self.initial_scroll:
            # Start a timer to enable the bottom bar after initial scroll completes
            if not hasattr(self, "initial_scroll_timer_set") or not self.initial_scroll_timer_set:
                Clock.schedule_once(self.handle_initial_scroll_complete, 2.0)  # 2 second delay
                self.initial_scroll_timer_set = True
            return
        
        # Get bottom bar state
        target_state = self.bottom_bar.visible
        target_height = SIZE.BOTTOM_BAR_HEIGHT if target_state else 0
        
        # Skip if already at target height or currently animating
        correct_height = abs(self.bottom_spacer.height - target_height) < 1
        correct_opacity = abs(self.bottom_bar.opacity - (1 if target_state else 0)) < 0.1
        
        if (correct_height and correct_opacity) or self.animating_spacer:
            return
            
        # Use the synchronized animation approach
        self.synchronized_animate(show_bottom_bar=target_state)
    
    def handle_initial_scroll_complete(self, dt):
        """
        After a delay from first scroll, allow bottom bar to appear.
        This ensures we don't show the bottom bar prematurely during initial loading.
        """
        # Allow the bottom bar to appear when needed
        self.initial_scroll = False
        self.scroll_container.initial_scroll = False
        
        # Reset tracking
        self.initial_scroll_timer_set = False
        
        # Evaluate current scroll position to determine if bottom bar should appear
        scrollable_height = self.scroll_container.scroll_view.children[0].height
        view_height = self.scroll_container.scroll_view.height
        max_scroll = scrollable_height - view_height
        current_y = self.scroll_container.scroll_view.scroll_y
        
        pixels_scrolled = (1 - current_y) * max_scroll
        self.scroll_container.last_pixels_scrolled = pixels_scrolled
        
        # Check if we need to show the bottom bar based on current scroll position
        if pixels_scrolled > self.scroll_container.scroll_threshold_pixels and not self.bottom_bar.visible:
            self.synchronized_animate(show_bottom_bar=True)

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
        
        # Reset all bottom bar/spacer states if we have a bottom bar
        if hasattr(self, "bottom_bar"):
            self.reset_bottom_bar_state()
            
            # Reset initial scroll state to prevent bottom bar from showing too early
            self.initial_scroll = True
            if hasattr(self, "scroll_container"):
                self.scroll_container.initial_scroll = True
            
            if not hasattr(self, "initial_scroll_timer_set"):
                self.initial_scroll_timer_set = False
    
    def on_enter(self) -> None:
        """Called when the screen is entered."""
        # Schedule a state check for bottom bar if we have one
        if hasattr(self, "bottom_bar"):
            Clock.schedule_once(lambda dt: self.check_for_bottom_spacer(), 0.5)
