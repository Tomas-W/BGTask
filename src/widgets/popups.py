import time
start_time = time.time()

from typing import Callable

from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from src.screens.home.home_widgets import TaskHeader, TaskGroupContainer, TaskLabel, TimeLabel

from src.widgets.buttons import ConfirmButton, CancelButton
from src.widgets.containers import CustomButtonRow
from src.widgets.fields import TextField, CustomSettingsField
from src.widgets.misc import Spacer

from src.utils.logger import logger

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

        # Store callbacks
        self._confirm_handler = None
        self._cancel_handler = None

    def _update_height(self, instance, value):
        """Update popup height based on content"""
        self.height = value + SPACE.SPACE_XL
    
    def _update_text_size(self, instance, value):
        """Update text_size to enable text wrapping based on width"""
        width = self.width - SPACE.SPACE_XL
        self.header.text_size = (width, None)
        
    def _update_label_height(self, instance, value):
        """Update label height to match its texture height"""
        texture_height = instance.texture_size[1]
        instance.height = texture_height
    
    def _safe_call(self, func: Callable, arg=None):
        """Call a function that might expect arguments"""
        import inspect
        if func:
            sig = inspect.signature(func)
            if len(sig.parameters) == 0:
                return func()
            else:
                return func(arg)
    
    def show_animation(self, *args):
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


class TaskPopup(BasePopup):
    """Popup with a Task and snooze/stop alarm buttons"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Header
        self.header = TaskHeader(text="Task Expired!")
        self.header.halign = "center"
        self.header.bind(texture_size=self._update_label_height)
        self.content_layout.add_widget(self.header)

        # Task spacer
        self.task_spacer = Spacer(height=SPACE.SPACE_XL)
        self.content_layout.add_widget(self.task_spacer)

        # Task header
        self.task_header = TaskHeader(text="")
        self.content_layout.add_widget(self.task_header)
        # Task container
        self.task_container = TaskGroupContainer()
        self.content_layout.add_widget(self.task_container)
        # Timestamp
        self.task_time = TimeLabel(text="")
        self.task_container.add_widget(self.task_time)
        # Task label
        self.task_label = TaskLabel(text="")
        self.task_container.add_widget(self.task_label)

        # Button spacer
        self.button_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.button_spacer)

        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CancelButton(text="Stop", width=2)
        self.button_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = ConfirmButton(text="Snooze", width=2)
        self.button_row.add_widget(self.confirm_button)
        # Add to layout
        self.content_layout.add_widget(self.button_row)

        self.bind(width=self._update_text_size)
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Un- and re-bind callbacks"""
        # Unbind callbacks
        if self._confirm_handler:
            self.confirm_button.unbind(on_release=self._confirm_handler)
        if self._cancel_handler:
            self.cancel_button.unbind(on_release=self._cancel_handler)
        
        # Create new handlers
        self._confirm_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_confirm)
        )
        self._cancel_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
        )
        
        # Bind new callbacks
        self.confirm_button.bind(on_release=self._confirm_handler)
        self.cancel_button.bind(on_release=self._cancel_handler)


class CustomPopup(BasePopup):
    """Popup with a message and confirm/cancel buttons"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
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
        # Field
        self.field = CustomSettingsField(text="", width=1, color_state=STATE.INACTIVE)
        self.content_layout.add_widget(self.field)

        # Field spacer
        self.field_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.field_spacer)

        # Extra info
        self.extra_info = Label(
            text="",
            color=COL.TEXT,
            font_size=FONT.DEFAULT,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=1,
            text_size=(None, None)
        )
        self.extra_info.bind(texture_size=self._update_label_height)
        self.content_layout.add_widget(self.extra_info)

        # Extra info spacer
        self.extra_info_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.extra_info_spacer)

        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = ConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        # Add to layout
        self.content_layout.add_widget(self.button_row)

        self.bind(width=self._update_text_size)
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Un- and re-bind callbacks"""
        # Unbind callbacks
        if self._confirm_handler:
            self.confirm_button.unbind(on_release=self._confirm_handler)
        if self._cancel_handler:
            self.cancel_button.unbind(on_release=self._cancel_handler)
        
        # Create new handlers
        self._confirm_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_confirm)
        )
        self._cancel_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
        )
        
        # Bind new callbacks
        self.confirm_button.bind(on_release=self._confirm_handler)
        self.cancel_button.bind(on_release=self._cancel_handler)

    def update_field_text(self, text: str):
        """Update the text displayed in the field"""
        self.field.label.text = text


class ConfirmationPopup(BasePopup):
    """Popup with a message and confirm/cancel buttons"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
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
        # Field
        self.field = CustomSettingsField(text="", width=1, color_state=STATE.INACTIVE)
        self.content_layout.add_widget(self.field)

        # Field spacer
        self.field_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.field_spacer)
        
        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = ConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        # Add to layout
        self.content_layout.add_widget(self.button_row)

        self.bind(width=self._update_text_size)
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Un- and re-bind callbacks"""
        # Unbind callbacks
        if self._confirm_handler:
            self.confirm_button.unbind(on_release=self._confirm_handler)
        if self._cancel_handler:
            self.cancel_button.unbind(on_release=self._cancel_handler)
        
        # Create new handlers
        self._confirm_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_confirm)
        )
        self._cancel_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
        )
        
        # Bind new callbacks
        self.confirm_button.bind(on_release=self._confirm_handler)
        self.cancel_button.bind(on_release=self._cancel_handler)

    def update_field_text(self, text: str):
        """Update the text displayed in the field"""
        self.field.label.text = text


class TextInputPopup(BasePopup):
    """Popup with a text input field and confirm/cancel buttons"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
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
        # Cancel button
        self.cancel_button = CancelButton(text="Cancel", width=2)
        self.button_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = ConfirmButton(text="Confirm", width=2)
        self.button_row.add_widget(self.confirm_button)
        # Add to layout
        self.content_layout.add_widget(self.button_row)
        
        self.bind(width=self._update_text_size)
    
    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Un- and re-bind callbacks"""
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


class PopupManager:
    def __init__(self):
        start_time = time.time()
        self.custom = CustomPopup()
        self.confirmation = ConfirmationPopup()
        self.input = TextInputPopup()
        self.task = TaskPopup()
        
        # Bind to task manager events
        from kivy.app import App
        app = App.get_running_app()
        self.task_manager = app.task_manager
        self.audio_manager = app.audio_manager
        self.task_manager.bind(on_task_expired_show_task_popup=self._handle_task_popup)
        
        total_time = time.time() - start_time
        logger.critical(f"Time taken to initialize PopupManager: {total_time}")
    
    def _handle_task_popup(self, *args, **kwargs):
        """Handle showing task popup when task expires."""
        logger.critical(f"Handling task popup: {args} {kwargs}")
        # Get task from either positional args or kwargs
        task = kwargs.get("task") if "task" in kwargs else args[0]
        
        def stop_alarm(*args):
            """Stop the alarm for the given task."""
            self.audio_manager.keep_alarming = False
            self.audio_manager.stop_playing_audio()
            self.audio_manager.current_alarm_path = None
            self.audio_manager.alarm_is_triggered = False
        
        self.task.update_callbacks(
            on_confirm=lambda *args: self.task_manager.on_task_popup_confirm(task),
            on_cancel=lambda *args: stop_alarm()
        )
        self.show_task_popup(task=task)

    def _handle_popup_confirmation(self, confirmed: bool):
        """Handle confirmation popup button press"""
        if self.callback:
            self.callback(confirmed)

    def _handle_popup_text_input(self, confirmed: bool):
        """Handle text input popup button press"""
        if self.callback:
            text = self.input.input_field.text if confirmed else None
            self.callback(text)
    
    def show_custom_popup(self, header: str, field_text: str, extra_info: str, confirm_text: str,
                          on_confirm: Callable, on_cancel: Callable):
        """Show a custom popup with a PartitionHeader (aligned center),
        ConfirmButton and CancelButton."""
        self.custom.header.text = header
        self.custom.extra_info.text = extra_info
        self.custom.update_field_text(field_text)
        self.custom.confirm_button.set_text(confirm_text)
        self.custom.update_callbacks(on_confirm, on_cancel)
        self.custom.show_animation()

    def show_confirmation_popup(self, header: str, field_text: str,
                                 on_confirm: Callable, on_cancel: Callable):
        """
        Show a confirmation popup with a PartitionHeader (aligned center),
        CustomConfirmButton and CustomCancelButton.
        Reuses the same popup instance for efficiency.
        """
        self.confirmation.header.text = header
        self.confirmation.update_field_text(field_text)
        self.confirmation.update_callbacks(on_confirm, on_cancel)
        self.confirmation.show_animation()

    def show_input_popup(self, header: str, input_text: str,
                         on_confirm: Callable, on_cancel: Callable):
        """
        Show a popup with an InputField between the header and buttons.
        Reuses the same popup instance for efficiency.
        """
        self.input.header.text = header
        self.input.input_field.text = input_text
        self.input.update_callbacks(on_confirm, on_cancel)
        self.input.show_animation()
    
    def show_task_popup(self, *args, **kwargs):
        """Show a task popup with a TaskHeader, TaskContainer, Timestamp, and TaskLabel."""
        # Get task from either positional args or kwargs
        task = kwargs.get("task") if "task" in kwargs else args[-1]
        
        # Ensure we're on the main thread and in a window context
        def show_popup(dt):
            # Set up the task popup
            self.task.task_header.text = task.timestamp.strftime("%A %d %B")
            self.task.task_time.text = task.timestamp.strftime("%H:%M")
            self.task.task_label.text = task.message
            
            # Force the popup to use the app's root window context
            from kivy.app import App
            app = App.get_running_app()
            
            # Close any existing popups
            if hasattr(app, 'active_popup') and app.active_popup:
                app.active_popup.dismiss()
                
            # Store reference and show
            app.active_popup = self.task
            self.task.show_animation()
        
        Clock.schedule_once(show_popup, 0)

    def _show_task_popup(self, task, on_confirm=None, on_cancel=None):
        """Show a task popup with the given callbacks."""
        logger.critical(f"Showing task popup for task: {task}")
        
        self.task.update_callbacks(
            on_confirm=on_confirm,
            on_cancel=on_cancel
        )
        self.show_task_popup(task=task)


POPUP = PopupManager()

total_time = time.time() - start_time
logger.critical(f"Time taken to initialize popups: {total_time}")