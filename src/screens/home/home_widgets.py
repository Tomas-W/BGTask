from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image

from src.settings import SPACE, SIZE, COL, STYLE, FONT, PATH


class TasksByDate(BoxLayout):
    """
    A TasksByDate is used to display all Tasks for a specific date.
    It has a TaskHeader on top, and a TaskGroupContainer below, which as a background.
    
    TasksByDate structure:
    - A TaskHeader
    - A TaskGroupContainer [vertical]
      |-- TaskContainer(s) [vertical]
          |-- A TimeLabelContainer [horizontal]
          |    |-- A TimeLabel [ Label (HH:MM) ]
          |    |-- An EditTaskButton [ Button (Edit) ]
          |    |-- A DeleteTaskButton [ Button (Delete) ]
          |
          |--A TaskLabel
    """
    def __init__(self, date_str, tasks, task_manager, parent_screen=None, **kwargs):
        super().__init__(
            orientation="vertical",
            **kwargs
        )
        self.task_manager = task_manager
        self.parent_screen = parent_screen
        
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
        time_container = TimeContainer()

        # Time & Icons
        time_label_container = TimeLabelContainer()
        # Time
        time_label = TimeLabel(text=task.get_time_str())
        time_label_container.add_widget(time_label)
        # Icons
        task_icon_container = TaskIconContainer()
        sound_icon = TaskIcon(source=PATH.SOUND_IMG)
        vibrate_icon = TaskIcon(source=PATH.VIBRATE_IMG)
        # Add icons to container
        task_icon_container.add_widget(sound_icon)
        task_icon_container.add_widget(vibrate_icon)
        # Add to container
        time_label_container.add_widget(task_icon_container)
        time_container.add_widget(time_label_container)

        # Edit Delete Container
        edit_delete_container = EditTaskButtonContainer()
        # Edit
        edit_button = EditTaskButton(text="Edit", type="edit")
        edit_button.bind(on_release=lambda x, task_id=task.task_id: self.task_manager.edit_task(task_id))
        edit_delete_container.add_widget(edit_button)
        # Delete    
        delete_button = EditTaskButton(text="Delete", type="delete")
        delete_button.bind(on_release=lambda x, task_id=task.task_id: self.task_manager.delete_task(task_id))
        edit_delete_container.add_widget(delete_button)
        # Add to container
        time_container.add_widget(edit_delete_container)
        
        # Register the buttons
        if self.parent_screen:
            self.parent_screen.register_edit_delete_button(edit_button)
            self.parent_screen.register_edit_delete_button(delete_button)
        
        
        
        
        
        task_label = TaskLabel(text=task.message)
        
        def update_text_size(instance, value):
            width = value[0]
            instance.text_size = (width, None)
            
            def adjust_height(dt):
                instance.height = instance.texture_size[1]
                task_container.height = time_label_container.height + instance.height
            
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
      |-- A TimeLabelContainer [horizontal]
      |    |-- A TimeLabel [ Label (HH:MM) ]
      |    |-- An EditTaskButton [ Button (Edit) ]
      |    |-- A DeleteTaskButton [ Button (Delete) ]
      |
      |--A TaskLabel
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=SPACE.SPACE_M,
            padding=[0, SPACE.SPACE_M, 0, SPACE.SPACE_M],
            **kwargs
        )
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
    A TaskContainer is used to group a TimeLabel, EditTaskButton, DeleteTaskButton,
     and a TaskLabel.
    
    TaskContainer structure:
    - A TimeLabelContainer [vertical]
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


class TimeContainer(BoxLayout):
    """
    A TimeContainer is a container for a TimeLabel, EditTaskButton, and DeleteTaskButton.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            **kwargs,
            # padding=[SPACE.FIELD_PADDING_X, 0, SPACE.FIELD_PADDING_X, 0],
        )


class TimeLabelContainer(BoxLayout):
    """
    TimeLabelContainer contains a TimeLabel, EditTaskButton, and DeleteTaskButton.

    TimeLabelContainer structure [horizontal]:
    - A TimeLabel [ Label (HH:MM) ]
    - An EditTaskButton [ Button (Edit) ]
    - A DeleteTaskButton [ Button (Delete) ]
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(0.8, None),
            height=FONT.DEFAULT,
            spacing=SPACE.SPACE_XS,
            padding=[SPACE.FIELD_PADDING_X, 0, SPACE.FIELD_PADDING_X, 0],
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
            height=FONT.DEFAULT,
            halign="left",
            # padding=[0, 0, SPACE.SPACE_XS, 0],
            font_size=FONT.DEFAULT,
            bold=True,
            color=COL.TEXT,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))

        with self.canvas.before:
            Color(*COL.FIELD_ACTIVE)
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


class TaskIconContainer(BoxLayout):
    """
    A TaskIconContainer is a container for a TaskIcon.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            padding=[0, 0, 0, SPACE.SPACE_XS],
            height=FONT.DEFAULT,
            # spacing=SPACE.SPACE_S,
            **kwargs
        )

        with self.canvas.before:
            Color(*COL.FIELD_ACTIVE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_S]
            )   
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class TaskIcon(Image):
    """
    A TaskIcon is a widget for displaying alarm info  icons in the TimeLabelContainer
    """
    def __init__(self, source="", **kwargs):
        super().__init__(
            source=source,
            size_hint=(1, 1),
            # pos_hint={"center_y": 0.5},
            # width=FONT.DEFAULT,
            # height=FONT.DEFAULT,
            opacity=1,
            **kwargs
        )

    def set_opacity(self, opacity: int):
        """Set the opacity of the icon (0 for hidden, 1 for visible)"""
        self.opacity = opacity
    
    def set_source(self, source: str):
        """Update the image source"""
        self.source = source


class EditTaskButtonContainer(BoxLayout):
    """
    A EditTaskButtonContainer is a container for an EditTaskButton.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            height=FONT.DEFAULT,
            spacing=SPACE.SPACE_S,
            padding=[0, 0, SPACE.FIELD_PADDING_X, 0],
            **kwargs
        )


class EditTaskButton(Button):
    """
    An EditTaskButton is a button for editing or deleting a Task.
    - Has an opacity of 0 by default
    - Has a disabled=True to prevent it from being clickable by default.
    """
    def __init__(self, text: str, type: str, **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            height=FONT.DEFAULT,
            font_size=FONT.SETTINGS_BUTTON,
            bold=False,
            color=COL.TEXT,
            background_color=COL.OPAQUE,
            opacity=0,
            disabled=True,
            **kwargs
        )
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
