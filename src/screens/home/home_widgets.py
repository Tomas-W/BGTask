from typing import TYPE_CHECKING
from datetime import datetime, timedelta

from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from src.utils.logger import logger

from managers.tasks.task import TaskGroup
from managers.device.device_manager import DM
from src.settings import SPACE, SIZE, COL, STYLE, FONT

if TYPE_CHECKING:
    from managers.tasks.task import Task
    from managers.app_task_manager import TaskManager
    from src.screens.home.home_screen import HomeScreen
    from src.screens.start.start_screen import StartScreen


class TaskGroupWidget(BoxLayout):
    """
    A TaskGroup is used to group all Tasks for a specific date.
    It has a TaskHeader on top, and a TaskGroupContainer below, which as a background
     and contains TaskContainers.
    Each TaskContainer contains a TimeContainer and a TaskLabel, and optionally
     TaskIcons for sound and/or vibrate.
    
    TaskGroup structure:
    - TaskGroupHeader
    - TaskGroupContainer [vertical]
      |-- TaskContainer(s) [vertical] [controls background]
          |-- TimeContainer [horizontal]
          |    |-- AlarmTimeContainer [horizontal]
          |        |-- TimeLabel [Label (HH:MM)]
          |        |-- TaskIcon [Sound icon] [optional]
          |        |-- TaskIcon [Vibrate icon] [optional]
          |    |-- SnoozeContainer [horizontal] [optional]
          |        |-- SnoozeLabel [Label (Snoozed: HH:MM)] [optional]
          |
          |-- TaskLabel [Task message]
    """
    def __init__(self, date_str: str, tasks: list["Task"], task_manager: "TaskManager",
                 parent_screen, clickable: bool = True, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            **kwargs
        )
        self.tasks: list["Task"] = tasks
        self.first_task: "Task" = self.tasks[0] if self.tasks else None
        self.last_task: "Task" = self.tasks[-1] if self.tasks else None
        self.task_manager: "TaskManager" = task_manager
        self.parent_screen: "HomeScreen" | "StartScreen" = parent_screen
        
        self.date_str: str = TaskGroup.get_task_group_header_text(date_str)
        day_header: TaskGroupHeader = TaskGroupHeader(text=self.date_str)
        self.add_widget(day_header)

        self.task_group_container: TaskGroupContainer = TaskGroupContainer()
        self.add_widget(self.task_group_container)
        
        for task in self.tasks:
            self.add_task_item(task, clickable=clickable)

        self.task_group_container.bind(height=self._update_height)

    def _update_height(self, instance, value):
        """Updates the height of the TaskGroupWidget by summing the heights of its children."""
        self.height = sum(child.height for child in self.children)

    def add_task_item(self, task, clickable: bool = True):
        """Adds a Task to the TaskGroupWidget."""
        is_first_task: bool = task == self.first_task
        is_last_task: bool = task == self.last_task
        expired: bool = datetime.now() > task.timestamp + timedelta(seconds=task.snooze_time)
        task_container = TaskContainer(expired=expired,
                                      is_first_task=is_first_task,
                                      is_last_task=is_last_task)
        
        # Time container
        time_container = TimeContainer()
        alarm_container = AlarmTimeContainer()
        time_container.add_widget(alarm_container)
        
        # Time label
        time_label = TimeLabel(text=task.get_time_str())
        alarm_container.add_widget(time_label)
        
        # Icons
        if task.alarm_name is not None:
            sound_icon = TaskIcon(source=DM.PATH.SOUND_IMG)
            alarm_container.add_widget(sound_icon)
        if task.vibrate:
            vibrate_icon = TaskIcon(source=DM.PATH.VIBRATE_IMG)
            alarm_container.add_widget(vibrate_icon)
        
        # Snooze setup if needed
        if task.snooze_time:
            spacer = BoxLayout(size_hint=(0.6, None))
            time_container.add_widget(spacer)
            
            snooze_container = SnoozeContainer()
            time_container.add_widget(snooze_container)
            
            snooze_icon = TaskIcon(source=DM.PATH.SNOOZE_IMG)
            snooze_container.add_widget(snooze_icon)
            snooze_label = SnoozeLabel(text=task.get_snooze_str())
            snooze_container.add_widget(snooze_label)
        
        # Task label
        task_label = TaskLabel(text=task.message, task=task, clickable=clickable)
        task_label.bind(size=self._on_task_label_size)
        
        # Set size for wrapping
        task_label.text_size = (task_container.width - (SPACE.TASK_PADDING_X * 2), None)
        task_label.texture_update()
        
        # Calculate initial height
        if is_first_task and is_last_task:
            padding_height = SPACE.TASK_PADDING_Y * 2
        elif is_first_task or is_last_task:
            padding_height = SPACE.TASK_PADDING_Y * 1.5
        else:
            padding_height = SPACE.TASK_PADDING_Y
        
        # Set initial heights
        task_label.height = task_label.texture_size[1]
        total_height = time_container.height + task_label.height + padding_height
        task_container.height = total_height
        
        # Add widgets
        task_container.add_widget(time_container)
        task_container.add_widget(task_label)
        self.task_group_container.add_widget(task_container)

    def _on_task_label_size(self, instance, value):
        """Updates the size of the TaskLabel."""
        # Update size for wrapping
        instance.text_size = (instance.width, None)
        instance.texture_update()
        
        # Get TaskContainer
        task_container = instance.parent
        if not task_container:
            return
        # Get TimeContainer
        time_container = task_container.children[-1]
        
        # Calculate padding
        if task_container.is_first_task and task_container.is_last_task:
            padding_height = SPACE.TASK_PADDING_Y * 2
        elif task_container.is_first_task or task_container.is_last_task:
            padding_height = SPACE.TASK_PADDING_Y * 1.5
        else:
            padding_height = SPACE.TASK_PADDING_Y
        
        # Update heights
        instance.height = instance.texture_size[1]
        task_container.height = time_container.height + instance.height + padding_height


class TaskGroupContainer(BoxLayout):
    """
    A TaskGroupContainer is used to group all Tasks for a specific date.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=0,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class TaskContainer(BoxLayout):
    """
    A TaskContainer is a container for a Task that shows its:
      - TimeLabel, Icons, SnoozeLabel
      - TaskLabel
      - Background color based on expired state
      - Has padding based on position [top|middle|bottom]
    """
    def __init__(self, expired: bool, is_first_task: bool, is_last_task: bool, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            **kwargs
        )
        self.is_first_task: bool = is_first_task
        self.is_last_task: bool = is_last_task
        self.bind(minimum_height=self.setter("height"))
        
        with self.canvas.before:
            self.bg_color = Color(*COL.FIELD_INPUT)  # Active by default
            self.bg_rect = Rectangle(
                pos=self.pos,
                size=self.size
            )
            self.bind(pos=self._update_bg, size=self._update_bg)
            
        # Padding based on position
        if is_first_task and is_last_task:
            self.padding = [SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y,
                          SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y]
        elif is_first_task:
            self.padding = [SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y,
                          SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y/2]
        elif is_last_task:
            self.padding = [SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y/2,
                          SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y]
        else:
            self.padding = [SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y/2,
                          SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y/2]
        
        self.set_expired(expired)

    def _update_bg(self, instance, value):
        """Updates the background size of the TaskContainer."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_expired(self, expired=True):
        """Sets the background color based on expired state."""
        if expired:
            self.bg_color.rgba = COL.FIELD_INACTIVE
        else:
            self.bg_color.rgba = COL.FIELD_INPUT


class TaskGroupHeader(Label):
    """
    A TaskGroupHeader displays the date of a TaskGroup, formats:
    - "Today, Jun 13"
    - "Monday 24 Mar"
    """
    def __init__(self, text: str,**kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            height=SIZE.HEADER_HEIGHT,
            halign="left",
            font_size=FONT.HEADER,
            bold=True,
            color=COL.TEXT_GREY,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))
    
    def set_text(self, text: str):
        self.text = text


class TimeContainer(BoxLayout):
    """
    A TimeContainer is a container for a TimeLabel, TaskIcons and SnoozeLabel.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            height=FONT.DEFAULT,
            spacing=SPACE.SPACE_S,
            **kwargs,
        )


class AlarmTimeContainer(BoxLayout):
    """
    A AlarmTimeContainer is a container for a TimeLabel and TaskIcons.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(0.4, None),
            height=FONT.DEFAULT,
            spacing=SPACE.SPACE_S,
            **kwargs,
        )


class TimeLabel(Label):
    """
    A TimeLabel displays the time of a Task.
    - Formatted as "HH:MM"
    """
    def __init__(self, text: str, **kwargs):
        super().__init__(
            text=text,
            size_hint=(None, None),
            height=FONT.DEFAULT,
            halign="left",
            font_size=FONT.DEFAULT,
            bold=True,
            color=COL.TEXT,
            **kwargs
        )
        self.texture_update()
        self.width = self.texture_size[0]
        self.bind(text=self._update_width)
    
    def _update_width(self, instance, value):
        """Updates the width when text changes."""
        self.texture_update()
        self.width = self.texture_size[0]


class TaskIcon(Image):
    """
    A TaskIcon is a widget for displaying alarm info icons
    """
    def __init__(self, source="", **kwargs):
        super().__init__(
            source=source,
            size_hint=(None, None),
            size=(FONT.DEFAULT*0.8, FONT.DEFAULT*0.8),
            pos_hint={"center_y": 0.5},
            opacity=1,
            **kwargs
        )


class SnoozeContainer(BoxLayout):
    """
    A SnoozeContainer is a container for a SnoozeIcon and SnoozeLabel.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(0.4, None),
            height=FONT.DEFAULT,
            spacing=SPACE.SPACE_XS,
            **kwargs,
        )


class SnoozeLabel(Label):
    """
    A SnoozeLabel displays the snooze time of a Task, formats:
    - "Snoozed: DD:HH"
    - "Snoozed: HH:MM"
    - "Snoozed: MM:SS"
    """
    def __init__(self, text: str, **kwargs):
        super().__init__(
            text=text,
            size_hint=(None, None),
            height=FONT.DEFAULT,
            halign="right",
            font_size=FONT.SMALL,
            bold=True,
            color=COL.SNOOZE,
            **kwargs
        )
        self.texture_update()
        self.width = self.texture_size[0]
        self.bind(text=self._update_width)
    
    def _update_width(self, instance, value):
        """Updates the width when text changes."""
        self.texture_update()
        self.width = self.texture_size[0]

class TaskLabel(Label):
    """
    A TaskLabel displays the contents of a Task.
    Can be clicked to select or deselect the Task.
    """
    def __init__(self, text: str, task=None, clickable: bool = True, **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            halign="left",
            valign="top",
            font_size=FONT.DEFAULT,
            color=COL.TEXT,
            **kwargs
        )
        self.task = task
        self.task_id = str(task.task_id) if task else None
        self.active = False
        self.selected = False
        self.clickable = clickable
        self.bind(size=self.setter("text_size"))

        with self.canvas.before:
            self.bg_color = Color(*COL.OPAQUE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_S]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
        """Updates the background size of the TaskLabel."""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def set_active(self, active=True):
        """Sets the background color based on active state."""
        self.active = active
        if active:
            self.bg_color.rgba = COL.FIELD_SELECTED
        else:
            if self.selected:
                self.bg_color.rgba = COL.FIELD_SELECTED
            else:
                self.bg_color.rgba = COL.OPAQUE
    
    def set_selected(self, selected=True):
        """Sets the background color based on selected state."""
        self.selected = selected
        if selected:
            self.bg_color.rgba = COL.FIELD_SELECTED
        else:
            if self.active:
                self.bg_color.rgba = COL.FIELD_SELECTED
            else:
                self.bg_color.rgba = COL.OPAQUE
    
    def on_touch_down(self, touch):
        """Handles the touch down event."""
        if not self.collide_point(*touch.pos) or not self.task_id or not self.clickable:
            return super().on_touch_down(touch)
        
        app = DM.get_app()
        task_manager = app.task_manager
        home_screen = app.get_screen(DM.SCREEN.HOME)
        task_to_select = self.task

        fresh_task = task_manager.get_task_by_id_(self.task_id)
        if fresh_task:
            task_to_select = fresh_task
        else:
            logger.error(f"Error selecting Task: {DM.get_task_id_log(self.task_id)} not found")
            return False
                
        home_screen.select_task(task_to_select, self)
        return True
