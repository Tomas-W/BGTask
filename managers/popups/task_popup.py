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
    """
    A TaskPopup has a:
    - Header
    - Task label
    - SnoozeAButton and SnoozeBButton
    - CancelButton
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_message_height = SIZE.TASK_POPUP_HEIGHT
        # Header
        self.header = TaskPopupHeader(text="Task Expired!")
        self.header.bind(texture_size=self._update_label_height)
        self.content_layout.add_widget(self.header)

        # Handlers
        self._snooze_a_handler: Callable | None = None
        self._snooze_b_handler: Callable | None = None

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

        # Snooze row
        self.snooze_row = CustomButtonRow()
        self.content_layout.add_widget(self.snooze_row)
        # Snooze A
        self.snooze_a_button = ConfirmButton(text="Snooze 1m", width=2)
        self.snooze_row.add_widget(self.snooze_a_button)
        # Snooze B
        self.snooze_b_button = ConfirmButton(text="Snooze 1h", width=2)
        self.snooze_row.add_widget(self.snooze_b_button)

        # Button spacer
        self.button_spacer = Spacer(height=SPACE.SPACE_M)
        self.content_layout.add_widget(self.button_spacer)
        
        # Cancel row
        self.cancel_row = CustomButtonRow()
        self.content_layout.add_widget(self.cancel_row)
        # Cancel
        self.cancel_button = CancelButton(text="Cancel", width=1)
        self.cancel_row.add_widget(self.cancel_button)
        # Add to layout
        

        self.bind(width=self._update_text_size)
    
    def _update_scroll_height(self, instance, size):
        """Update the height of both container and ScrollView based on label height"""
        label_height = size[1]
        new_height = min(self.min_message_height, label_height)
        self.task_label_container.height = new_height
        self.scroll_view.height = new_height
        instance.height = label_height

    def update_callbacks(self, snooze_a: Callable, snooze_b: Callable, cancel: Callable):
        """Un- and re-bind callbacks"""
        # Unbind callbacks
        if self._snooze_a_handler:
            self.snooze_a_button.unbind(on_release=self._snooze_a_handler)
        if self._snooze_b_handler:
            self.snooze_b_button.unbind(on_release=self._snooze_b_handler)
        if self._cancel_handler:
            self.cancel_button.unbind(on_release=self._cancel_handler)
        
        # Create new handlers
        self._snooze_a_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(snooze_a)
        )
        self._snooze_b_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(snooze_b)
        )
        self._cancel_handler = lambda x: self.hide_animation(
            on_complete=lambda *args: self._safe_call(cancel)
        )
        
        # Bind new callbacks
        self.snooze_a_button.bind(on_release=self._snooze_a_handler)
        self.snooze_b_button.bind(on_release=self._snooze_b_handler)
        self.cancel_button.bind(on_release=self._cancel_handler)
