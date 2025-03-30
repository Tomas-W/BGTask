from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from src.settings import SPACE, SIZE, COL, STYLE, FONT, SCREEN


class TasksbyDate(BoxLayout):
    """
    A TasksbyDate is used to display all Tasks for a specific date.
    It has a TaskHeader on top, and a TaskGroupContainer below, which as a background.
    
    TasksbyDate structure:
    - A TaskHeader [ Label (Monday 24 Mar) ]
    - A TaskGroupContainer [ BoxLayout - TaskContainers ]
      |-- TaskContainer(s) [ BoxLayout - time Label, task Label ]
          |-- A TimeLabelContainer [ BoxLayout - time Label, edit button, delete button ]
          |    |-- A TimeLabel [ Label (HH:MM) ]
          |    |-- An EditTaskButton [ Button (Edit) ]
          |    |-- A DeleteTaskButton [ Button (Delete) ]
          |
          |--A TaskLabel [ Label (Task message) ]
    """
    def __init__(self, date_str, tasks, **kwargs):
        super().__init__(**kwargs)
        self.task_manager = App.get_running_app().task_manager
        self.orientation = "vertical"
        
        day_header = TaskHeader(text=date_str)
        self.add_widget(day_header)
        
        self.tasks_container = TaskGroupContainer()
        for task in tasks:
            self.add_task_item(task)
        self.add_widget(self.tasks_container)
        
        self.tasks_container.bind(height=self._update_height)
    
    def _update_height(self, instance, value):
        self.height = sum(child.height for child in self.children)
    
    def add_task_item(self, task):
        task_container = TaskContainer()
        time_container = TimeLabelContainer()
        
        time_label = TimeLabel(text=task.get_time_str())
        time_label.set_size_hint_x(0.3)
        
        edit_button = EditTaskButton(text="Edit", type="edit")
        edit_button.set_size_hint_x(0.3)
        edit_button.bind(on_press=lambda x, task_id=task.task_id: self.task_manager.edit_task(task_id))
        
        delete_button = EditTaskButton(text="Delete", type="delete")
        delete_button.set_size_hint_x(0.3)
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
    A TaskGroupContainer is used to group all Tasks for a specific date,
    and place a background behind them.
    
    TaskGroupContainer structure:
    - TaskContainer(s) [ BoxLayout - time Label, task Label ]
      |-- A TimeLabelContainer [ BoxLayout - time Label, edit button, delete button ]
      |    |-- A TimeLabel [ Label (HH:MM) ]
      |    |-- An EditTaskButton [ Button (Edit) ]
      |    |-- A DeleteTaskButton [ Button (Delete) ]
      |
      |--A TaskLabel [ Label (Task message) ]
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
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class TaskContainer(BoxLayout):
    """
    A TaskContainer is used to group a time label, edit button, delete button,
     and a task label.
    
    TaskContainer structure:
    - A TimeLabelContainer [ BoxLayout - time Label, edit button, delete button ]
      |-- A TimeLabel [ Label (HH:MM) ]
      |-- An EditTaskButton [ Button (Edit) ]
      |-- A DeleteTaskButton [ Button (Delete) ]
    - A TaskLabel [ Label (Task message) ]
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


class TimeLabelContainer(BoxLayout):
    """
    TimeLabelContainer contains a time label, edit button, and delete button.

    TimeLabelContainer structure:
    - A TimeLabel [ Label (HH:MM) ]
    - An EditTaskButton [ Button (Edit) ]
    - A DeleteTaskButton [ Button (Delete) ]
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
    A TimeLabel displays the time of a Task.
    - Formatted as "HH:MM"
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
    
    def set_size_hint_x(self, value: float):
        self.size_hint_x = value


class EditTaskButton(Button):
    """
    An EditTaskButton is a button for editing or deleting a Task.
    - Has an opacity of 0 by default
    - Has a disabled=True to prevent it from being clickable by default.
    - Can be switched on and off using the switch_opacity and switch_disabled methods.
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
        home_screen.edit_delete_buttons.append(self)

        self.type = type
        self.bg_color = COL.FIELD_PASSED if type == "edit" else COL.ERROR
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_S]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def set_size_hint_x(self, value: float):
        self.size_hint_x = value
    
    def set_opacity(self, opacity: int):
        self.opacity = int(opacity)
    
    def set_disabled(self, disabled: bool):
        self.disabled = disabled

    def switch_opacity(self):
        self.opacity = int(not self.opacity)
    
    def switch_disabled(self):
        self.disabled = not self.disabled


class TaskLabel(Label):
    """
    A TaskLabel displays the contents of a Task.
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
