from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from src.settings import SPACE, SIZE, COL, STYLE, FONT, SCREEN


class TaskGroup(BoxLayout):
    """
    TaskGroup is the base for tasks grouped by date that:
    - Displays a day header
    - Displays tasks in a TaskGroupContainer
    """
    def __init__(self, date_str, tasks, **kwargs):
        super().__init__(**kwargs)
        self.task_manager = App.get_running_app().task_manager
        self.orientation = "vertical"
        
        # Header with day name and int
        day_header = TaskHeader(text=date_str)
        self.add_widget(day_header)
        
        # Tasks container
        self.tasks_container = TaskGroupContainer()
        for task in tasks:
            self.add_task_item(task)
        self.add_widget(self.tasks_container)
        
        self.tasks_container.bind(height=self._update_height)
    
    def _update_height(self, instance, value):
        """Update the overall height when tasks_container height changes"""
        height = 0
        for child in self.children:
            height += child.height
        self.height = height
    
    def add_task_item(self, task):
        """Add a task item widget"""
        # Time stamp (+ edit and delete) and task message
        task_container = TaskContainer()
        time_container = TimeLabelContainer()

        time_label = TimeLabel(text=task.get_time_str())
        time_label.size_hint_x = 0.3
        
        edit_button = EditTaskButton(text="Edit", type="edit")
        edit_button.size_hint_x = 0.3
        edit_button.bind(on_press=lambda x, task_id=task.task_id: self.task_manager.edit_task(task_id))
        
        delete_button = EditTaskButton(text="Delete", type="delete")
        delete_button.size_hint_x = 0.3
        delete_button.bind(on_press=lambda x, task_id=task.task_id: self.task_manager.delete_task(task_id))

        time_container.add_widget(time_label)
        time_container.add_widget(edit_button)
        time_container.add_widget(delete_button)
        
        task_label = TaskLabel(text=task.message)
        
        def update_text_size(instance, value):
            width = value[0]
            instance.text_size = (width, None)
            
            def adjust_height(dt):
                instance.height = instance.texture_size[1]
                task_container.height = time_container.height + instance.height
            
            # Height adjustment for next frame
            Clock.schedule_once(adjust_height, 0)
        
        task_label.bind(size=update_text_size)
        
        task_container.add_widget(time_container)
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
            self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
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
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            height=SIZE.TASK_ITEM_HEIGHT,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


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


class TimeLabelContainer(BoxLayout):
    """
    TimeLabelContainer is the base for a time label that:
    - Contains a time label
    - Contains an EditTaskButton [hidden by default]
    - Contains a DeleteTaskButton [hidden by default]
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            height=SIZE.TIME_LABEL_HEIGHT,
            spacing=SPACE.FIELD_PADDING_X,
            padding=[0, 0, SPACE.FIELD_PADDING_X, 0],
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


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


class EditTaskButton(Button):
    """
    Button for editing or deleting a task
    - Has an opacity of 0 by default
    - Has a button=False to prevent it from being clickable
    """
    def __init__(self, text: str, type: str, **kwargs):
        super().__init__(
            text=text,
            size_hint_y=None,
            height=SIZE.TIME_LABEL_HEIGHT,
            font_size=FONT.SETTINGS_BUTTON,
            bold=False,
            color=COL.TEXT,
            background_color=COL.OPAQUE,
            opacity=0,
            disabled=True,
            **kwargs
        )
        home_screen = App.get_running_app().get_screen(SCREEN.HOME)
        if not self in home_screen.edit_delete_buttons:
            home_screen.edit_delete_buttons.append(self)

        self.type = type
        self.bg_color = COL.FIELD_PASSED if type == "edit" else COL.FIELD_ERROR
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_S]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
        """Update background rectangle on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def switch_opacity(self):
        """Switch the opacity of the button"""
        self.opacity = int(not self.opacity)
    
    def switch_disabled(self):
        """Switch the disabled state of the button"""
        self.disabled = not self.disabled


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
