import time
start_time = time.time()

from datetime import timedelta
from typing import Callable

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect

from src.screens.home.home_widgets import (TaskHeader, TaskGroupContainer,
                                           TaskLabel, TimeLabel)

from src.widgets.buttons import ConfirmButton, CancelButton
from src.widgets.containers import CustomButtonRow
from src.widgets.fields import TextField, CustomSettingsField
from src.widgets.misc import Spacer

from src.utils.logger import logger

from src.settings import COL, SPACE, FONT, STATE, SIZE, LOADED
from managers.device.device_manager import DM

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
        self.min_message_height = SIZE.TASK_POPUP_HEIGHT
        # Header
        self.header = TaskHeader(text="Task Expired!")
        self.header.halign = "center"
        self.header.bind(texture_size=self._update_label_height)
        self.content_layout.add_widget(self.header)

        # Task spacer
        self.task_spacer = Spacer(height=SPACE.SPACE_XL)
        self.content_layout.add_widget(self.task_spacer)

        # Task container
        self.task_container = TaskGroupContainer()
        self.task_container.spacing = 0
        self.content_layout.add_widget(self.task_container)
        
        # Timestamp
        self.task_time = TimeLabel(text="")
        self.task_container.add_widget(self.task_time)
        
        # Container for scrollable Task label
        self.task_label_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=self.min_message_height  # Bound to min(min_message_height, label_height)
        )
        
        # ScrollView for Task label
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            effect_cls=ScrollEffect,
            size_hint=(1, None),
            height=self.min_message_height  # Bound to min(min_message_height, label_height)
        )
        
        # Task label
        self.task_label = TaskLabel(text="")
        self.task_label.bind(
            texture_size=self._update_scroll_height,
            size=lambda instance, size: setattr(instance, 'text_size', (size[0], None))
        )
        
        # Add task label to scroll view
        self.scroll_view.add_widget(self.task_label)
        self.task_label_container.add_widget(self.scroll_view)
        self.task_container.add_widget(self.task_label_container)

        # Button spacer
        self.button_spacer = Spacer(height=SPACE.SPACE_L)
        self.content_layout.add_widget(self.button_spacer)

        # Button row
        self.button_row = CustomButtonRow()
        # Stop button
        self.stop_alarm = CancelButton(text="Stop", width=2)
        self.button_row.add_widget(self.stop_alarm)
        # Snooze button
        self.snooze_alarm = ConfirmButton(text="Snooze 1m", width=2)
        self.button_row.add_widget(self.snooze_alarm)
        # Add to layout
        self.content_layout.add_widget(self.button_row)

        self.bind(width=self._update_text_size)
    
    def _update_scroll_height(self, instance, size):
        """Update the height of both container and ScrollView based on label height"""
        label_height = size[1]
        new_height = min(self.min_message_height, label_height)
        self.task_label_container.height = new_height
        self.scroll_view.height = new_height
        instance.height = label_height

    def update_callbacks(self, on_confirm: Callable, on_cancel: Callable):
        """Un- and re-bind callbacks"""
        # Unbind callbacks
        if self._confirm_handler:
            self.snooze_alarm.unbind(on_release=self._confirm_handler)
        if self._cancel_handler:
            self.stop_alarm.unbind(on_release=self._cancel_handler)
        
        # Create new handlers
        self._confirm_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_confirm)
        )
        self._cancel_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(on_cancel) if on_cancel else None
        )
        
        # Bind new callbacks
        self.snooze_alarm.bind(on_release=self._confirm_handler)
        self.stop_alarm.bind(on_release=self._cancel_handler)


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
        
        # Managers
        from kivy.app import App
        app = App.get_running_app()
        self.task_manager = app.task_manager
        self.task_manager.expiry_manager.bind(on_task_expired_show_task_popup=self._handle_task_popup)
    	
        LOADED.POPUP_MANAGER = True
    
    def _handle_task_popup(self, *args, **kwargs):
        """
        Handle showing TaskPopup when a Task expires.
        Configures callbacks for:
        - Stop alarm
        - Snooze alarm
        """
        task = kwargs.get("task") if "task" in kwargs else args[0]
        if not task:
            logger.error("No task provided to _handle_task_popup")
            return
        
        # Update popup callbacks
        self.task.update_callbacks(
            on_confirm=lambda: self._snooze_alarm(task.task_id),
            on_cancel=lambda: self._stop_alarm(task.task_id)
        )
        
        # Show the popup
        self.show_task_popup(task=task)
    
    def _stop_alarm(self, task_id: str):
        """Stop the alarm and mark task as expired"""
        from kivy.app import App
        app = App.get_running_app()
        expiry_manager = app.task_manager.expiry_manager
        
        expiry_manager.cancel_task(task_id=task_id)
    
    def _snooze_alarm(self, task_id: str):
        """Snooze the alarm"""
        from kivy.app import App
        app = App.get_running_app()
        expiry_manager = app.task_manager.expiry_manager
        
        expiry_manager.snooze_task(DM.ACTION.SNOOZE_A, task_id)

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
        """
        Show a CustomPopup with a:
        - Header [aligned left]
        - Info field
        - Extra info [aligned left]
        - ConfirmButton and CancelButton.
        """
        self.custom.header.text = header
        self.custom.extra_info.text = extra_info
        self.custom.update_field_text(field_text)
        self.custom.confirm_button.set_text(confirm_text)
        self.custom.update_callbacks(on_confirm, on_cancel)
        self.custom.show_animation()

    def show_confirmation_popup(self, header: str, field_text: str,
                                 on_confirm: Callable, on_cancel: Callable):
        """
        Show a ConfirmationPopup with a:
        - Header [aligned left]
        - Info field
        - ConfirmButton and CancelButton.
        Reuses the same popup instance for efficiency.
        """
        self.confirmation.header.text = header
        self.confirmation.update_field_text(field_text)
        self.confirmation.update_callbacks(on_confirm, on_cancel)
        self.confirmation.show_animation()

    def show_input_popup(self, header: str, input_text: str,
                         on_confirm: Callable, on_cancel: Callable):
        """
        Show a TextInputPopup with a:
        - Header [aligned left]
        - Input field
        - ConfirmButton and CancelButton.
        Reuses the same popup instance for efficiency.
        """
        self.input.header.text = header
        self.input.input_field.text = input_text
        self.input.update_callbacks(on_confirm, on_cancel)
        self.input.show_animation()
    
    def show_task_popup(self, *args, **kwargs):
        """
        Show a TaskPopup with a:
        - Header [aligned center]
        - TaskContainer
          |- TimeLabel
          |- TaskLabel
        - StopButton and SnoozeButton
        """
        task = kwargs.get("task") if "task" in kwargs else args[-1]
        logger.critical(f"show_task_popup popup for task: {task}")
        
        def show_popup(dt):
            time = task.timestamp + timedelta(seconds=task.snooze_time)
            self.task.task_time.text = time.strftime(DM.DATE.TASK_TIME)
            self.task.task_label.text = task.message
            
            from kivy.app import App
            app = App.get_running_app()
            
            def display_new_popup(dt):
                app.active_popup = self.task
                self.task.show_animation()
            
            # Close any existing popups
            if hasattr(app, "active_popup") and app.active_popup:
                app.active_popup.dismiss()
                # Schedule new popup to show after a small delay
                Clock.schedule_once(display_new_popup, 0.3)
            else:
                # No existing popup, show immediately
                display_new_popup(0)
        
        Clock.schedule_once(show_popup, 0)

    def _show_task_popup(self, task, on_confirm=None, on_cancel=None):
        """Internal callback for handling the TaskPopup."""
        logger.critical(f"Showing task popup for task: {task}")
        
        self.task.update_callbacks(
            on_confirm=on_confirm,
            on_cancel=on_cancel
        )
        self.show_task_popup(task=task)


from src.utils.timer import TIMER
TIMER.start("PopupManager")

POPUP = PopupManager()

TIMER.stop("PopupManager")
logger.timing(f"Loading PopupManager took: {TIMER.get_time('PopupManager')}")