from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.uix.label import Label
from typing import Callable
from src.widgets.containers import CustomButtonRow
from src.widgets.buttons import CustomConfirmButton, CustomCancelButton
from src.widgets.labels import PartitionHeader
from src.widgets.fields import TextField

from src.settings import COL, SPACE, SIZE, FONT


class BasePopup(Popup):
    """Base class for all popups"""
    def __init__(self, **kwargs):
        # Create content layout
        self.content_layout = BoxLayout(
            orientation="vertical",
            spacing=SPACE.SPACE_M,
            size_hint=(1, None),
        )
        
        super().__init__(
            title="",  # No title - we use our own header
            content=self.content_layout,
            size_hint=(1, None),
            background="",  # Remove default background
            background_color=COL.BG_POPUP,  # Set background color
            separator_height=0,  # No separator
            auto_dismiss=False,  # Don't close on outside click
            **kwargs
        )

        
        # Add padding after border
        self.content_layout.padding = [SPACE.SCREEN_PADDING_X, SPACE.SPACE_L]

    
    def on_content_size(self, *args):
        """Adjust popup height based on content"""
        self.height = self.content_layout.minimum_height + dp(20)
    
    def show_animation(self):
        """Show popup with fade animation"""
        self.opacity = 0
        self.open()
        
        anim = Animation(opacity=1, duration=0.3)
        anim.start(self)
    
    def hide_animation(self, on_complete=None):
        """Hide popup immediately and call callback"""
        self.dismiss()
        if on_complete:
            on_complete()


class ConfirmationPopup(BasePopup):
    """Popup with a message and confirm/cancel buttons"""
    def __init__(self, header: str,
                 on_cancel: Callable, on_confirm: Callable, **kwargs):
        super().__init__(**kwargs)
        
        # Single header for the message
        self.header = Label(
            text=header,
            color=COL.TEXT,
            font_size=FONT.DEFAULT,
            halign="left",
            valign="middle",
            size_hint=(1, None),  # Allow height to adjust
            text_size=(None, None)  # Will be set when size changes
        )
        # Bind size updates for text wrapping and height adjustment
        self.header.bind(
            width=lambda *_: setattr(self.header, "text_size", (self.header.width, None)),
            texture_size=lambda *_: setattr(self.header, "height", self.header.texture_size[1] + dp(20))
        )
        self.content_layout.add_widget(self.header)
        
        # Button row
        self.button_row = CustomButtonRow()
        
        # Cancel button
        self.cancel_button = CustomCancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        
        # Confirm button
        self.confirm_button = CustomConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        
        self.content_layout.add_widget(self.button_row)
        
        # Set initial callbacks
        self.update_callbacks(on_confirm, on_cancel)
        
        # Update height after adding all widgets
        self.bind(on_open=lambda *args: self.on_content_size())
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Update button callbacks with proper unbinding"""
        # Unbind existing callbacks
        self.confirm_button.unbind(on_release=self.confirm_button.on_release)
        self.cancel_button.unbind(on_release=self.cancel_button.on_release)
        
        # Bind new callbacks
        self.confirm_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: on_confirm()
            )
        )
        self.cancel_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: on_cancel()
            )
        )


class TextInputPopup(BasePopup):
    """Popup with a text input field and confirm/cancel buttons"""
    def __init__(self, header: str, input_text: str,
                 on_cancel: Callable, on_confirm: Callable, **kwargs):
        super().__init__(**kwargs)
        
        # Single header for the message
        self.header = Label(
            text=header,
            color=COL.TEXT,
            font_size=FONT.DEFAULT,
            halign="left",
            valign="middle",
            size_hint=(1, None),  # Allow height to adjust
            text_size=(None, None)  # Will be set when size changes
        )
        # Bind size updates for text wrapping and height adjustment
        self.header.bind(
            width=lambda *_: setattr(self.header, "text_size", (self.header.width, None)),
            texture_size=lambda *_: setattr(self.header, "height", self.header.texture_size[1] + dp(20))
        )
        self.content_layout.add_widget(self.header)
        
        # Input field
        self.input_field = TextField(
            hint_text=input_text,
            n_lines=1
        )
        self.content_layout.add_widget(self.input_field)
        
        # Button row
        self.button_row = CustomButtonRow()
        
        # Cancel button
        self.cancel_button = CustomCancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        
        # Confirm button
        self.confirm_button = CustomConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        
        self.content_layout.add_widget(self.button_row)
        
        # Set initial callbacks
        self.update_callbacks(on_confirm, on_cancel)
        
        # Update height after adding all widgets
        self.bind(on_open=lambda *args: self.on_content_size())
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Update button callbacks with proper unbinding"""
        # Unbind existing callbacks
        self.confirm_button.unbind(on_release=self.confirm_button.on_release)
        self.cancel_button.unbind(on_release=self.cancel_button.on_release)
        
        # Bind new callbacks
        self.confirm_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: on_confirm()
            )
        )
        self.cancel_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: on_cancel()
            )
        )
