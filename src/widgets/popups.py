from typing import Callable

from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from src.widgets.buttons import CustomConfirmButton, CustomCancelButton
from src.widgets.containers import CustomButtonRow
from src.widgets.fields import TextField, CustomSettingsField
from src.widgets.misc import Spacer

from src.settings import COL, SPACE, FONT, STATE


class BasePopup(Popup):
    """Base class for all popups"""
    def __init__(self, **kwargs):
        # Holds the Widgets
        self.content_layout = BoxLayout(
            orientation="vertical",
            padding=[SPACE.SPACE_S, SPACE.SPACE_S, SPACE.SPACE_S, SPACE.SPACE_L],
        )
        
        super().__init__(
            title="",
            content=self.content_layout,
            size_hint=(1, None),
            height=1,
            background="",
            background_color=COL.BG_POPUP,
            separator_height=0,
            auto_dismiss=False,
            **kwargs
        )
        self.content_layout.bind(minimum_height=self._update_height)

    def _update_height(self, instance, value):
        """Update popup height based on content"""
        self.height = value + SPACE.SPACE_XL
    
    def _update_text_size(self, instance, value):
        """Update text_size to enable text wrapping based on width"""
        width = self.width - SPACE.SPACE_XL
        self.header.text_size = (width, None)
        
    def _update_label_height(self, instance, value):
        """Update label height to match its texture height plus padding"""
        texture_height = instance.texture_size[1]
        instance.height = texture_height
    
    def _safe_call(self, func: Callable, arg=None):
        """Safely call a function that might expect arguments or not"""
        import inspect
        if func:
            sig = inspect.signature(func)
            if len(sig.parameters) == 0:
                return func()
            else:
                return func(arg)
    
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
    def __init__(self, header: str, field_text: str,
                 on_cancel: Callable, on_confirm: Callable, **kwargs):
        super().__init__(**kwargs)
        
        # Header
        self.header = Label(
            text=header,
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
        # Field
        self.field = CustomSettingsField(text=field_text, width=1, color_state=STATE.INACTIVE)
        self.content_layout.add_widget(self.field)

        # Field spacer
        self.field_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.field_spacer)
        
        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomCancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = CustomConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        # Add to layout
        self.content_layout.add_widget(self.button_row)

        self.update_callbacks(on_confirm, on_cancel)
        self.bind(width=self._update_text_size)
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Update button callbacks with proper unbinding"""
        # Unbind existing callbacks
        self.confirm_button.unbind(on_release=self.confirm_button.on_release)
        self.cancel_button.unbind(on_release=self.cancel_button.on_release)
        
        # Bind new callbacks
        self.confirm_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: self._safe_call(on_confirm)
            )
        )
        self.cancel_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
            )
        )

    def update_field_text(self, text: str):
        """Update the text displayed in the field"""
        self.field.label.text = text


class TextInputPopup(BasePopup):
    """Popup with a text input field and confirm/cancel buttons"""
    def __init__(self, header: str, input_text: str,
                 on_cancel: Callable, on_confirm: Callable, **kwargs):
        super().__init__(**kwargs)
        
        # Header
        self.header = Label(
            text=header,
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
            hint_text=input_text,
            n_lines=1,
        )
        self.content_layout.add_widget(self.input_field)

        # Input field spacer
        self.input_field_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.input_field_spacer)
        
        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomCancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = CustomConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        # Add to layout
        self.content_layout.add_widget(self.button_row)
        
        self.update_callbacks(on_confirm, on_cancel)
        self.bind(width=self._update_text_size)
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Update button callbacks with proper unbinding"""
        # Unbind existing callbacks
        self.confirm_button.unbind(on_release=self.confirm_button.on_release)
        self.cancel_button.unbind(on_release=self.cancel_button.on_release)
        
        # Bind new callbacks
        self.confirm_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: self._safe_call(on_confirm, self.input_field.text)
            )
        )
        self.cancel_button.bind(
            on_release=lambda x: self.hide_animation(
                on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
            )
        )
