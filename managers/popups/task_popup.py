from typing import Callable

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect

from managers.popups.base_popup import BasePopup
from managers.popups.popup_widgets import TaskPopupHeader, TaskPopupLabel, TaskPopupContainer

from src.settings import SPACE, SIZE
from src.widgets.buttons import ConfirmButton, CancelButton
from src.widgets.containers import CustomButtonRow
from src.widgets.misc import Spacer


class TaskPopup(BasePopup):
    """Popup with a Task and snooze/stop alarm buttons"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_message_height = SIZE.TASK_POPUP_HEIGHT
        # Header
        self.header = TaskPopupHeader(text="Task Expired!")
        self.header.bind(texture_size=self._update_label_height)
        self.content_layout.add_widget(self.header)

        # Task spacer
        self.task_spacer = Spacer(height=SPACE.SPACE_M)
        self.content_layout.add_widget(self.task_spacer)

        # Task container
        self.task_container = TaskPopupContainer()
        self.content_layout.add_widget(self.task_container)
        
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
        self.task_label = TaskPopupLabel()
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