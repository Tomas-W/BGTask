from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from src.settings import SPACE, SIZE, COL, STYLE, FONT


class TaskGroup(BoxLayout):
    """
    TaskGroup is the base for tasks grouped by date that:
    - Displays a day header
    - Displays tasks in a TaskGroupContainer
    """
    def __init__(self, date_str, tasks, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        # Header with day name and int
        day_header = TaskHeader(text=date_str)
        self.add_widget(day_header)
        
        # Tasks container
        self.tasks_container = TaskGroupContainer()
        for task in tasks:
            self.add_task_item(task)
        self.add_widget(self.tasks_container)
        
        self.height = day_header.height + self.tasks_container.height
        self.tasks_container.bind(height=self.update_group_height)
    
    def update_group_height(self, instance, value):
        """Update the overall height when tasks_container height changes"""
        self.height = SPACE.SPACE_XS + SIZE.HEADER_HEIGHT + value
    
    def add_task_item(self, task):
        """Add a task item widget"""
        # Time stamp and task message
        task_container = TaskContainer()
        time_label = TimeLabel(text=task.get_time_str())
        task_label = TaskLabel(text=task.message)
        
        def update_text_size(instance, value):
            width = value[0]
            instance.text_size = (width, None)
            
            def adjust_height(dt):
                instance.height = instance.texture_size[1]
                
                task_container.height = time_label.height + instance.height
            
            # Schedule the height adjustment for next frame
            Clock.schedule_once(adjust_height, 0)
        
        task_label.bind(size=update_text_size)
        
        task_container.add_widget(time_label)
        task_container.add_widget(task_label)
        self.tasks_container.add_widget(task_container)


class TaskGroupContainer(BoxLayout):
    """
    TaskGroupContainer is the base for all tasks in a day that:
    - Contains TaskContainers
    - Has a rounded rectangle background
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.spacing = SPACE.SPACE_M
        self.padding = [0, SPACE.SPACE_M, 0, SPACE.SPACE_M]
        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(*COL.FIELD_ACTIVE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_M]
            )
            self.bind(pos=self._update, size=self._update)

    def _update(self, instance, value):
        """Update background rectangle on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class TaskContainer(BoxLayout):
    """
    TaskContainer is the base for a task item that:
    - Contains a time label
    - Contains a task label
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = SIZE.TASK_ITEM_HEIGHT


class TaskHeader(Label):
    """
    TaskHeader displays the day of the week and the date
    - Formatted as "Monday 22"
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


class TimeLabel(Label):
    """
    TimeLabel displays the time of a task
    """
    def __init__(self, text: str, **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            height=SIZE.TIME_LABEL_HEIGHT,
            halign="left",
            font_size=FONT.DEFAULT,
            bold=True,
            color=COL.TEXT,
            padding=[SPACE.FIELD_PADDING_X, 0, SPACE.FIELD_PADDING_X, 0],
            **kwargs
        )
        self.bind(size=self.setter("text_size"))


class TaskLabel(Label):
    """
    TaskLabel displays the contents of a task
    """
    def __init__(self, text: str, **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            halign="left",
            valign="top",
            font_size=FONT.DEFAULT,
            color=COL.TEXT,
            padding=[SPACE.FIELD_PADDING_X, 0],
            **kwargs
        )
        self.bind(size=self.setter("text_size"))
