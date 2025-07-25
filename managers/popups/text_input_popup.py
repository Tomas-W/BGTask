from typing import Callable

from kivy.uix.label import Label

from managers.device.device_manager import DM
from managers.popups.base_popup import BasePopup

from src.widgets.buttons import ConfirmButton, CancelButton
from src.widgets.containers import CustomButtonRow
from src.widgets.fields import TextField
from src.widgets.misc import Spacer

from src.settings import COL, FONT, SPACE


class TextInputPopup(BasePopup):
    """
    A TextInputPopup has a:
    - Header
    - Input field
    - Confirm and Cancel buttons
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _init_content(self):
        """
        Initialize the content of the TextInputPopup.
        """
        # Header
        self.header = Label(
            text="",
            color=COL.TEXT,
            font_size=FONT.DEFAULT,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=1,
            text_size=(None, None)
        )
        self.header.bind(texture_size=self._update_label_height)
        self.content_layout.add_widget(self.header)
        # Input field
        self.input_field = TextField(
            hint_text="",
            n_lines=1,
        )
        self.content_layout.add_widget(self.input_field)

        # Input field spacer
        self.input_field_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.input_field_spacer)
        
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

        DM.LOADED.INPUT_POPUP = True
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable) -> None:
        """Un- and re-bind callbacks."""
        # Unbind callbacks
        if self._confirm_handler:
            self.confirm_button.unbind(on_release=self._confirm_handler)
        if self._cancel_handler:
            self.cancel_button.unbind(on_release=self._cancel_handler)
        
        # Create new handlers
        self._confirm_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_confirm, self.input_field.text)
        )
        self._cancel_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
        )
        
        # Bind new callbacks
        self.confirm_button.bind(on_release=self._confirm_handler)
        self.cancel_button.bind(on_release=self._cancel_handler)