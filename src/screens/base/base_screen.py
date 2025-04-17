from typing import Callable

from kivy.animation import Animation, AnimationTransition
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from src.widgets.bars import TopBarClosed, TopBarExpanded, BottomBar
from src.widgets.containers import BaseLayout, ScrollContainer
from src.widgets.misc import Spacer
from src.widgets.popups import ConfirmationPopup, TextInputPopup, CustomPopup

from src.utils.logger import logger

from src.settings import SCREEN, SIZE, COL


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
        self.top_bar_is_expanded = False  # TopBar or TopBarExpanded
        self.initial_scroll = True        # Prevent BottomBar untill user scrolls
        self.animating_spacer = False     # If spacer is animating
        self.pending_bar_check = None     # Timer for debounced bottom bar visibility

        self.popup_text: str | None = None

        # Initialize popup instances with None callbacks
        self.custom_popup = CustomPopup(
            header="",
            field_text="",
            extra_info="",
            confirm_text="",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )
        self.confirmation_popup = ConfirmationPopup(
            header="",
            field_text="",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )
        self.text_input_popup = TextInputPopup(
            header="",
            input_text="",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )

        # Use RelativeLayout instead of FloatLayout
        # RelativeLayout works similar to FloatLayout but is more efficient
        self.root_layout = RelativeLayout()
        
        # Main content container
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
        
        # ScrollContainer
        self.scroll_container = ScrollContainer(
            parent_screen=self,
            scroll_callback=self.check_bottom_bar_state,
            allow_scroll_y=True,
            allow_scroll_x=False
        )

        # BottomBar
        self.bottom_bar = None
        
        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)
    
    def add_bottom_bar(self):
        """
        Add a bottom bar to the screen to scroll to the top.
        Includes a Spacer that is in sync with the BottomBar animation.
        """
        # BottomBar
        self.bottom_bar = BottomBar(text="^")
        self.bottom_bar.bind(on_release=self.scroll_container.scroll_to_top)
        self.root_layout.add_widget(self.bottom_bar)
        
        # Spacer
        self.bottom_spacer = Spacer(height=0, color=COL.BG)
        self.layout.add_widget(self.bottom_spacer)
        
        # Hide BottomBar
        self.bottom_bar.opacity = 0
        self.bottom_bar.visible = False
        self.bottom_bar.pos_hint = {"center_x": 0.5, "y": -0.15}
    
    def reset_bottom_bar_state(self):
        """Hide the BottomBar and Spacer."""
        if self.bottom_bar is not None:
            # Cancel any pending animations or checks
            if self.pending_bar_check:
                Clock.unschedule(self.pending_bar_check)
                self.pending_bar_check = None
            
            self.bottom_bar.opacity = 0
            self.bottom_bar.pos_hint = {"center_x": 0.5, "y": -0.15}
            self.bottom_bar.visible = False
            self.bottom_spacer.height = 0
            self.animating_spacer = False
        
        # Reset scroll container's tracking too
        self.scroll_container.last_pixels_scrolled = 0
    
    def check_bottom_bar_state(self, *args) -> None:
        """
        This is called when the scroll position changes or when bar visibility state changes.
        Synchronizes spacer animation with bottom bar animation if conditions are met.
        """
        # Prevent bottom bar from showing before users first scroll
        if self.initial_scroll:
            return
        
        # Cancel any pending check to avoid rapid changes when user keeps scrolling
        if self.pending_bar_check:
            Clock.unschedule(self.pending_bar_check)
        
        # Schedule a new check with a small delay to debounce rapid scrolling
        self.pending_bar_check = Clock.schedule_once(self._do_check_bottom_bar_state, 0.1)

    def _do_check_bottom_bar_state(self, *args) -> None:
        """Actual implementation of the bottom bar check after debouncing"""
        self.pending_bar_check = None
        
        # Prevent bottom bar from showing before users first scroll
        if self.initial_scroll:
            return
        
        target_state = self.bottom_bar.visible
        target_height = SIZE.BOTTOM_BAR_HEIGHT if target_state else 0        
        correct_height = abs(self.bottom_spacer.height - target_height) < 1
        correct_opacity = abs(self.bottom_bar.opacity - (1 if target_state else 0)) < 0.1
        # Skip if at target height or animating
        if (correct_height and correct_opacity) or self.animating_spacer:
            return
            
        # Apply animation
        self.bottom_bar_animation(show_bottom_bar=target_state)

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

        # Reset BottomBar
        self.initial_scroll = True
        self.reset_bottom_bar_state()
    
    def on_enter(self) -> None:
        """Called when the screen is entered."""
        # When entering the screen, hide BottomBar untill first scroll
        if self.initial_scroll:
            Clock.schedule_once(lambda *args: setattr(self, "initial_scroll", False), 0.5)

    def bottom_bar_animation(self, show_bottom_bar):
        """Synchronize the bottom bar and spacer animations."""
        self.animating_spacer = True
        self.bottom_bar.visible = show_bottom_bar
        
        duration = 0.3
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
        
        # Reset animation flag
        spacer_anim.bind(on_complete=lambda *args: setattr(self, "animating_spacer", False))
        
        # Start animations
        bar_anim.start(self.bottom_bar)
        spacer_anim.start(self.bottom_spacer)
    
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
        
    def _handle_popup_confirmation(self, confirmed: bool):
        """Handle confirmation popup button press"""
        if self.callback:
            self.callback(confirmed)

    def _handle_popup_text_input(self, confirmed: bool):
        """Handle text input popup button press"""
        if self.callback:
            text = self.text_input_popup.input_field.text if confirmed else None
            self.callback(text)
    
    def show_custom_popup(self, header: str, field_text: str, extra_info: str, confirm_text: str,
                          on_confirm: Callable, on_cancel: Callable):
        """Show a custom popup with a PartitionHeader (aligned center),
        ConfirmButton and CancelButton."""
        self.custom_popup.header.text = header
        self.custom_popup.extra_info.text = extra_info
        self.custom_popup.update_field_text(field_text)
        self.custom_popup.confirm_button.set_text(confirm_text)
        self.custom_popup.update_callbacks(on_confirm, on_cancel)
        self.custom_popup.show_animation()

    def show_confirmation_popup(self, header: str, field_text: str,
                                 on_confirm: Callable, on_cancel: Callable):
        """
        Show a confirmation popup with a PartitionHeader (aligned center),
        CustomConfirmButton and CustomCancelButton.
        Reuses the same popup instance for efficiency.
        """
        self.confirmation_popup.header.text = header
        self.confirmation_popup.update_field_text(field_text)
        self.confirmation_popup.update_callbacks(on_confirm, on_cancel)
        self.confirmation_popup.show_animation()

    def show_text_popup(self, header: str, input_text: str,
                         on_confirm: Callable, on_cancel: Callable):
        """
        Show a popup with an InputField between the header and buttons.
        Reuses the same popup instance for efficiency.
        """
        self.text_input_popup.header.text = header
        self.text_input_popup.input_field.text = input_text
        self.text_input_popup.update_callbacks(on_confirm, on_cancel)
        self.text_input_popup.show_animation()

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