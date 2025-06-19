from typing import TYPE_CHECKING

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from src.utils.logger import logger

from managers.tasks.task import TaskGroup
from managers.device.device_manager import DM
from src.settings import SPACE, SIZE, COL, FONT

if TYPE_CHECKING:
    from managers.tasks.task import Task


class TaskGroupWidget(BoxLayout):
    """
    A TaskGroupWidget is a container for a TaskGroup.
    TaskGroupWidget
      |-- TaskGroupHeader   [Label]
      |-- TaskInfoContainer [BoxLayout]
          |-- TaskInfo      [Label][background]
          |-- ...
    """
    def __init__(self, task_group: TaskGroup, clickable: bool = True, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            **kwargs
        )
        self.task_group: TaskGroup = task_group
        self.clickable: bool = clickable
        self.tasks = task_group.tasks

        self.header = TaskGroupHeader(text=task_group.date_str)
        self.add_widget(self.header)

        self.task_info_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=0,
        )
        self.add_widget(self.task_info_container)
        
        self.task_info_container.bind(minimum_height=self.task_info_container.setter("height"))
        self.task_info_container.bind(height=self._update_height)
        
        for i, task in enumerate(task_group.tasks):
            # First and last for padding purposes
            is_first_task = i == 0
            is_last_task = i == len(task_group.tasks) - 1
            self._add_task_info(task, is_first_task, is_last_task)
    
    def _update_height(self, instance, value):
        """Updates the height of the TaskGroupWidget by summing the children's heights."""
        self.height = sum(child.height for child in self.children)
    
    def _add_task_info(self, task: "Task", is_first_task: bool, is_last_task: bool):
        """Adds a TaskInfoLabel to the TaskInfoContainer."""
        time = task.get_time_str()
        snooze_time = f"+ {task.get_snooze_str()}" if task.snooze_time else ""
        message = task.message
        expired = task.expired
        
        # RGBA to hex
        text_color = "#{:02x}{:02x}{:02x}".format(
            int(COL.TEXT[0] * 255), int(COL.TEXT[1] * 255), int(COL.TEXT[2] * 255))
        snooze_color = "#{:02x}{:02x}{:02x}".format(
            int(COL.SNOOZE[0] * 255), int(COL.SNOOZE[1] * 255), int(COL.SNOOZE[2] * 255))

        # Format time, snooze and message
        task_info_text = f"[size={FONT.DEFAULT}][color={text_color}][b]{time}[/b][/color][/size]  [size={FONT.SMALL}][color={snooze_color}]{snooze_time}[/color][/size][size={FONT.DEFAULT}]\n[color={text_color}]{message}[/color][/size]"

        task_info_label = TaskInfoLabel(text=task_info_text,
                                      is_first_task=is_first_task,
                                      is_last_task=is_last_task,
                                      expired=expired,
                                      task=task,
                                      clickable=self.clickable)
        self.task_info_container.add_widget(task_info_label)


class TaskInfoLabel(Label):
    """
    A TaskInfoLabel is a label for displaying task info.
    """
    def __init__(self, text: str, is_first_task: bool, is_last_task: bool, expired: bool, task: "Task" = None, clickable: bool = True, **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            halign="left",
            valign="top",
            font_size=FONT.DEFAULT,
            color=COL.TEXT,
            markup=True,
            **kwargs
        )

        self.task = task
        self.task_id = str(task.task_id) if task else None
        self.selected = False
        self.is_first_task: bool = is_first_task
        self.is_last_task: bool = is_last_task
        self.clickable: bool = clickable

        # Bind width to update text_size for proper wrapping
        self.bind(width=self._update_text_size)
        # Bind texture_size to update height
        self.bind(texture_size=self._update_height)
        
        with self.canvas.before:
            self.bg_color = Color(*COL.TASK_ACTIVE)
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

    def _update_text_size(self, instance, value):
        """Updates text_size when width changes to enable proper text wrapping."""
        if self.width > 0:
            # Use full width - Label handles padding internally
            self.text_size = (self.width, None)

    def _update_height(self, instance, value):
        """Updates the widget height based on the texture size."""
        if self.texture_size[1] > 0:
            # Use texture height directly - Label handles padding internally
            self.height = self.texture_size[1]

    def _update_bg(self, instance, value):
        """Updates the background size of the TaskContainer."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_expired(self, expired=True):
        """Sets the background color based on expired state."""
        if expired:
            self.bg_color.rgba = COL.TASK_INACTIVE
        else:
            self.bg_color.rgba = COL.TASK_ACTIVE
    
    def set_selected(self, selected=True):
        """
        Sets the background color based on selected state.
        Used to display whether the Task is selected.
        """
        self.selected = selected
        if selected:
            self.bg_color.rgba = COL.TASK_SELECTED
        else:
            # When deselecting, check if task is expired
            if self.task and self.task.expired:
                self.bg_color.rgba = COL.TASK_INACTIVE
            else:
                self.bg_color.rgba = COL.TASK_ACTIVE
    
    def on_touch_down(self, touch):
        """Handles the touch down event."""
        if not self.collide_point(*touch.pos) or not self.task_id or not self.clickable:
            return super().on_touch_down(touch)
        
        # Find the home screen through the widget hierarchy
        home_screen = self._find_home_screen()
        if not home_screen:
            logger.error("Could not find HomeScreen for task selection")
            return False
            
        task_manager = home_screen.task_manager
        task_to_select = self.task

        fresh_task = task_manager.get_task_by_id_(self.task_id)
        if fresh_task:
            task_to_select = fresh_task
        else:
            logger.error(f"Error selecting Task: {DM.get_task_id_log(self.task_id)} not found")
            return False
                
        home_screen.select_task(task_to_select, self)
        return True
    
    def _find_home_screen(self):
        """Finds the HomeScreen by traversing up the widget hierarchy."""
        current = self
        while current:
            if hasattr(current, "name") and current.name == DM.SCREEN.HOME:
                return current
            current = current.parent
        return None


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
