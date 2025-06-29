from typing import Callable

from kivy.clock import Clock
from kivy.effects.scroll import ScrollEffect
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from managers.popups.base_popup import BasePopup
from managers.device.device_manager import DM

from src.widgets.buttons import ConfirmButton, CancelButton, SettingsButton
from src.widgets.containers import CustomButtonRow
from src.widgets.misc import Spacer

from src.settings import COL, FONT, SPACE, SIZE, STATE


class SelectionPopup(BasePopup):

    MAX_VISIBLE_BUTTONS = 7

    """
    A SelectionPopup has a:
    - Header
    - Scrollable list of SettingsButton widgets
    - Confirm and Cancel buttons
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _init_content(self):
        """
        Initialize the content of the SelectionPopup.
        """
        # Selection
        self.selected_button = None
        self.selected_value = None
        self.scroll_position = 1.0
        # Scroll view height
        self.max_visible_buttons = SelectionPopup.MAX_VISIBLE_BUTTONS
        self.button_spacing = SPACE.SPACE_S
        
        # Header
        self.header = Label(
            text="",
            color=COL.TEXT_GREY,
            font_size=FONT.HEADER,
            bold=True,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=1,
            text_size=(None, None)
        )
        self.header.bind(texture_size=self._update_label_height)
        self.content_layout.add_widget(self.header)
        
        # Header spacer
        self.header_spacer = Spacer(height=SPACE.SPACE_M)
        self.content_layout.add_widget(self.header_spacer)
        
        # ScrollView for selection buttons
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            effect_cls=ScrollEffect,
            size_hint=(1, None),
            height=self._get_content_height(self.max_visible_buttons)
        )
        
        # Container for selection buttons
        self.buttons_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            spacing=self.button_spacing
        )
        
        self.scroll_view.add_widget(self.buttons_container)
        self.content_layout.add_widget(self.scroll_view)
        
        # Selection spacer
        self.selection_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.selection_spacer)
        
        # Button row
        self.button_row = CustomButtonRow()
        self.content_layout.add_widget(self.button_row)
        # Cancel button
        self.cancel_button = CancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = ConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        # Bind
        self.bind(width=self._update_text_size)

        DM.LOADED.SELECTION_POPUP = True
    
    def _get_content_height(self, num_buttons: int) -> float:
        """Calculate height of content based on number of buttons and spacing."""
        if num_buttons == 0:
            return 0
        
        button_heights = num_buttons * SIZE.SETTINGS_BUTTON_HEIGHT
        spacing_heights = (num_buttons - 1) * self.button_spacing if num_buttons > 1 else 0
        return button_heights + spacing_heights
    
    def populate_selection_buttons(self, options_list: list[str], current_selection: str) -> None:
        """
        Add selection buttons to the scroll view.
        If alarm already selected:
        - Highlight it
        - Scroll to old position
        Otherwise:
        - Scroll to top
        """
        # Clear existing buttons
        self.buttons_container.clear_widgets()
        self.selected_button = None
        self.selected_value = None

        # Create buttons
        for option in options_list:
            button = SettingsButton(
                text=option,
                width=1,
                color_state=STATE.INACTIVE if option != current_selection else STATE.ACTIVE
            )
            button.bind(on_press=lambda btn, opt=option: self._on_button_press(btn, opt))
            self.buttons_container.add_widget(button)
            
            # Set selected
            if option == current_selection:
                self.selected_button = button
                self.selected_value = option
        
        # Update container height
        total_content_height = self._get_content_height(len(options_list))
        self.buttons_container.height = total_content_height
        
        # Update scroll view height
        visible_buttons = min(len(options_list), self.max_visible_buttons)
        scroll_height = self._get_content_height(visible_buttons)
        self.scroll_view.height = scroll_height
        
        def go_to_scroll_position(dt: float) -> None:
            self.scroll_view.scroll_y = self.scroll_position
        
        has_selected_button = current_selection in options_list
        # Reset to top when no selected button
        # Otherwise stay at old position
        if not has_selected_button:
            self.scroll_position = 1.0
            Clock.schedule_once(go_to_scroll_position, 0.01)
    
    def _on_button_press(self, button_instance, option_value):
        """Handle button selection:
        - Deselect previously selected button
        - Select new button
        """
        # Deselect previously selected button
        if self.selected_button:
            self.selected_button.set_inactive_state()
        
        # Select new button
        self.selected_button = button_instance
        self.selected_value = option_value
        button_instance.set_active_state()
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable) -> None:
        """Un- and re-bind callbacks"""
        # Unbind callbacks
        if self._confirm_handler:
            self.confirm_button.unbind(on_release=self._confirm_handler)
        if self._cancel_handler:
            self.cancel_button.unbind(on_release=self._cancel_handler)
        
        # Create new handlers
        self._confirm_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_confirm, self.selected_value)
        )
        self._cancel_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
        )
        
        # Bind new callbacks
        self.confirm_button.bind(on_release=self._confirm_handler)
        self.cancel_button.bind(on_release=self._cancel_handler)
