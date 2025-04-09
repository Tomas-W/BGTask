from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from src.utils.misc import get_task_header_text

from src.settings import SPACE, SIZE, COL, STYLE, FONT, PATH


class TasksByDate(BoxLayout):
    """
    A TasksByDate is used to display all Tasks for a specific date.
    It has a TaskHeader on top, and a TaskGroupContainer below, which as a background.
    
    TasksByDate structure:
    - A TaskHeader
    - A TaskGroupContainer [vertical]
      |-- TaskContainer(s) [vertical]
          |-- A TimeContainer [horizontal]
          |    |-- A TimeLabel [ Label (HH:MM) ]
          |    |-- A TaskIconContainer [horizontal]
          |    |    |-- A TaskIcon [ sound icon ]
          |    |    |-- A TaskIcon [ vibrate icon ]
          |    |-- A EditTaskButtonContainer [horizontal]
          |    |    |-- An EditTaskButton [ edit button ]
          |    |    |-- A DeleteTaskButton [ delete button ]
          |
          |--A TaskLabel [Task message]
    """
    def __init__(self, date_str, tasks, task_manager, parent_screen=None, **kwargs):
        super().__init__(
            orientation="vertical",
            **kwargs
        )
        self.task_manager = task_manager
        self.parent_screen = parent_screen
        self.tasks = tasks  # Store reference to tasks
        self.all_expired = False  # Track if all tasks are expired
        self.date_str = date_str

        # Format date string using cached function
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
            self.all_expired = True  # Mark this container as having all expired tasks
        
        self.tasks_container.bind(height=self._update_height)
    
    def _update_height(self, instance, value):
        self.height = sum(child.height for child in self.children)
    
    def add_task_item(self, task):
        task_container = TaskContainer()
        time_container = TimeContainer()

        # Time
        time_label = TimeLabel(text=task.get_time_str())
        time_container.add_widget(time_label)

        # Icons
        task_icon_container = TaskIconContainer()
        # Sound
        if task.alarm_name is not None:
            sound_icon = TaskIcon(source=PATH.SOUND_IMG)
            task_icon_container.add_widget(sound_icon)
        # Vibrate
        if task.vibrate:
            vibrate_icon = TaskIcon(source=PATH.VIBRATE_IMG)
            task_icon_container.add_widget(vibrate_icon)
        # Add to container
        time_container.add_widget(task_icon_container)

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
      |    |-- A TaskIconContainer [sound, vibrate]
      |    |    |-- A TaskIcon [sound icon]
      |    |    |-- A TaskIcon [vibrate icon]
      |    |-- A EditTaskButtonContainer [edit, delete]
      |    |    |-- An EditTaskButton [edit button]
      |    |    |-- A DeleteTaskButton [delete button]
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
    A TaskContainer is used to group a TimeLabel, EditTaskButton, DeleteTaskButton,
     and a TaskLabel.
    
    TaskContainer structure:
    - A TimeContainer [vertical]
      |-- A TimeLabel [ HH:MM ]
      |-- A TaskIconContainer [sound, vibrate]
      |    |-- A TaskIcon [sound icon]
      |    |-- A TaskIcon [vibrate icon]
      |-- A EditTaskButtonContainer [edit, delete]
      |    |-- An EditTaskButton [edit button]
      |    |-- A DeleteTaskButton [delete button]
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
    A TimeContainer is a container for a TimeLabel, EditTaskButton, and DeleteTaskButton.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            height=FONT.DEFAULT,
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
            padding=[0, 0, SPACE.FIELD_PADDING_X, 0],
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

class TaskIconContainer(BoxLayout):
    """
    A TaskIconContainer is a container for TaskIcons with fixed width for 2 icons
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(None, None),
            height=FONT.DEFAULT,
            spacing=SPACE.SPACE_S,
            padding=[0, 0, SPACE.SPACE_XS, 0],
            **kwargs
        )
        
        # Calculate fixed width for 2 icons
        icon_width = FONT.DEFAULT * 0.8
        self.width = (icon_width * 2) + SPACE.SPACE_S + self.padding[0] + self.padding[2]
    
    def add_widget(self, widget, *args, **kwargs):
        """Override to maintain fixed width when widgets are added"""
        super().add_widget(widget, *args, **kwargs)

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
        self.last_bound_args = None  # Will store the task_id
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_S]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def bind(self, **kwargs):
        """Override bind to capture task_id for remove_edit_buttons_for_group"""
        if 'on_release' in kwargs and callable(kwargs['on_release']):
            # Extract task_id from lambda function (if present)
            # This assumes the lambda contains a task_id parameter
            func_str = str(kwargs['on_release'])
            if 'task_id=' in func_str:
                # Store the task_id for later use
                self.last_bound_args = [func_str.split('task_id=')[1].split(')')[0]]
        
        return super().bind(**kwargs)

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
            **kwargs
        )
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
        if active:
            self.bg_color.rgba = COL.FIELD_ACTIVE
        else:
            self.bg_color.rgba = COL.OPAQUE

