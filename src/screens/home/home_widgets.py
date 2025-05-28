from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from src.utils.misc import get_task_header_text
from src.utils.logger import logger
from kivy.app import App

from src.managers.app_device_manager import DM
from src.settings import SPACE, SIZE, COL, STYLE, FONT, SCREEN


class TasksByDate(BoxLayout):
    """
    A TasksByDate is used to display all Tasks for a specific date.
    It has a TaskHeader on top, and a TaskGroupContainer below, which as a background
     and contains TaskContainers.
    Each TaskContainer contains a TimeContainer and a TaskLabel, and optionally
     TaskIcons for sound and/or vibrate.
    
    TasksByDate structure:
    - A TaskHeader
    - A TaskGroupContainer [vertical]
      |-- TaskContainer(s) [vertical]
          |-- A TimeContainer [horizontal]
          |    |-- A TimeLabel [ Label (HH:MM) ]
          |    |-- A TaskIcon [ sound icon ]
          |    |-- A TaskIcon [ vibrate icon ]
          |
          |--A TaskLabel [Task message]
    """
    def __init__(self, date_str, tasks, task_manager, parent_screen=None, **kwargs):
        super().__init__(
            orientation="vertical",
            **kwargs
        )
        self.task_manager = task_manager
        self.parent_screen = parent_screen  # HomeScreen
        self.tasks = tasks                  # List of Task objects
        self.all_expired = False
        self.date_str = date_str            # Formatted date string [Monday 24 Mar]

        self.date_str = get_task_header_text(date_str)
        day_header = TaskHeader(text=self.date_str)
        self.add_widget(day_header)
        
        self.tasks_container = TaskGroupContainer()
        for task in tasks:
            self.add_task_item(task)
        self.add_widget(self.tasks_container)
        
        # Set background color to FIELD_INACTIVE if all tasks are expired
        if tasks and all(task.expired for task in tasks):
            self.tasks_container.set_expired(True)
            self.all_expired = True
        
        self.tasks_container.bind(height=self._update_height)
    
    def _update_height(self, instance, value):
        self.height = sum(child.height for child in self.children)
    
    def add_task_item(self, task):
        task_container = TaskContainer()
        task_container.task = task
        task_container.task_id = task.task_id

        time_container = TimeContainer()
        # Time
        time_label = TimeLabel(text=task.get_time_str())
        time_container.add_widget(time_label)

        # Sound
        if task.alarm_name is not None:
            sound_icon = TaskIcon(source=DM.PATH.SOUND_IMG)
            time_container.add_widget(sound_icon)
        # Vibrate
        if task.vibrate:
            vibrate_icon = TaskIcon(source=DM.PATH.VIBRATE_IMG)
            time_container.add_widget(vibrate_icon)
        
        task_label = TaskLabel(text=task.message, task=task)
        
        def update_text_size(instance, value):
            width = value[0]
            instance.text_size = (width, None)
            
            def adjust_height(dt):
                instance.height = instance.texture_size[1]
                task_container.height = time_container.height + instance.height
            
            Clock.schedule_once(adjust_height, 0)
        
        task_label.bind(size=update_text_size)
        
        task_container.add_widget(time_container)
        task_container.add_widget(task_label)
        self.tasks_container.add_widget(task_container)


class TaskGroupContainer(BoxLayout):
    """
    A TaskGroupContainer is used to group all Tasks for a specific date,
    and place a background behind them.

    TaskGroupContainer structure:
    - TaskContainer(s) [vertical]
      |-- A TimeContainer [horizontal]
      |    |-- A TimeLabel [ HH:MM ]
      |    |-- A TaskIcon [sound icon]
      |    |-- A TaskIcon [vibrate icon]
      |
      |--A TaskLabel [Task message]
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=SPACE.SPACE_M,
            padding=[SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y],
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))
        
        with self.canvas.before:
            self.bg_color = Color(*COL.FIELD_ACTIVE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_M]
            )
            self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

        
    def set_expired(self, expired=True):
        """Set the container's background color based on expired state"""
        if expired:
            self.bg_color.rgba = COL.FIELD_INACTIVE
        else:
            self.bg_color.rgba = COL.FIELD_ACTIVE


class TaskContainer(BoxLayout):
    """
    A TaskContainer is used to group a TimeContainer, and a TaskLabel.
    
    TaskContainer structure:
    - A TimeContainer [vertical]
      |-- A TimeLabel [ HH:MM ]
      |-- A TaskIcon [sound icon]
      |-- A TaskIcon [vibrate icon]
      
    - A TaskLabel [Task message]
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            height=SIZE.TASK_ITEM_HEIGHT,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class TaskHeader(Label):
    """
    A TaskHeader displays the date of the Tasks in a TasksbyDate.
    - Formatted as "Monday 24 Mar"
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
    A TimeContainer is a container for a TimeLabel, and TaskIcons.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
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
        """Update width when text changes"""
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
        # Try prevent black img
        self._source = source
        self._app = None
    
    # Try prevent black img
    def on_parent(self, *args):
        """Called when widget is added to parent"""
        if self.parent and not self._app:
            self._app = App.get_running_app()
            if self._app:
                self._app.bind(on_resume=self._on_app_resume)
    
    # Try prevent black img
    def _on_app_resume(self, *args):
        """Called when app resumes from background"""
        if self._source:
            # Force reload the image
            self.source = ""  # Clear current source
            Clock.schedule_once(lambda dt: self._reload_image(), 0.1)

    # Try prevent black img
    def _reload_image(self):
        """Reload the image from source"""
        if self._source:
            self.source = self._source

    # Try prevent black img
    def __del__(self):
        """Clean up bindings when widget is destroyed"""
        if self._app:
            self._app.unbind(on_resume=self._on_app_resume)

    def set_opacity(self, opacity: int):
        """Set the opacity of the icon (0 for hidden, 1 for visible)"""
        self.opacity = opacity
    
    def set_source(self, source: str):
        """Update the image source"""
        self.source = source


class TaskLabel(Label):
    """
    A TaskLabel displays the contents of a Task.
    When tapped, it will be selected for editing or deletion.
    """
    def __init__(self, text: str, task=None, **kwargs):
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
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def set_active(self, active=True):
        """Set the background color based on active state"""
        self.active = active
        if active:
            self.bg_color.rgba = COL.FIELD_SELECTED
        else:
            if self.selected:
                self.bg_color.rgba = COL.FIELD_SELECTED
            else:
                self.bg_color.rgba = COL.OPAQUE
    
    def set_selected(self, selected=True):
        """Set the background color based on selected state"""
        self.selected = selected
        if selected:
            self.bg_color.rgba = COL.FIELD_SELECTED
        else:
            if self.active:
                self.bg_color.rgba = COL.FIELD_SELECTED
            else:
                self.bg_color.rgba = COL.OPAQUE
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or not self.task_id:
            return super().on_touch_down(touch)
        
        app = App.get_running_app()
        task_manager = app.task_manager
        home_screen = app.get_screen(SCREEN.HOME)
        task_to_select = self.task

        fresh_task = task_manager.get_task_by_id(self.task_id)
        if fresh_task:
            task_to_select = fresh_task
        else:
            logger.error(f"Task with id {self.task_id} not found in on_touch_down")
            return False
                
        home_screen.select_task(task_to_select, self)
        return True
