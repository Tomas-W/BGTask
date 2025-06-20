from typing import TYPE_CHECKING

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from managers.device.device_manager import DM

from src.screens.select_date.select_date_widgets import DateTimeLabel
from managers.tasks.task import TaskGroup
from src.utils.logger import logger
from src.settings import SPACE, SIZE, COL, FONT, STATE
from src.widgets.buttons import SettingsButton

if TYPE_CHECKING:
    from src.screens.home.home_screen import HomeScreen
    from src.managers.app_task_manager import TaskManager
    from managers.tasks.task import Task, TaskGroup


class NavigatorContainer(BoxLayout):
    """
    A WeekNavigatorContainer is a container for the week navigator.
    It allows the user to navigate between weeks.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class TaskNavigator(BoxLayout):
    """
    A TaskNavigator is a container for TaskGroup navigation.
    It allows the user to navigate between TaskGroups.
    """
    def __init__(self, task_group: "TaskGroup", task_manager: "TaskManager", **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            spacing=SPACE.SPACE_S,
            padding=[SPACE.SCREEN_PADDING_X, SPACE.SCREEN_PADDING_X],
            **kwargs
        )
        self.task_group: "TaskGroup" = task_group
        self.task_manager: "TaskManager" = task_manager
        self.current_week_start = None  # Track the current displayed week

        self.week_navigator_container = NavigatorContainer()
        self.add_widget(self.week_navigator_container)

        self.prev_week_button = SettingsButton(
            text="<",
            width=0.4,
            symbol=True,
            color_state=STATE.ACTIVE,
            color=COL.TEXT,
            bg_color=COL.TASK_SELECTED,
        )
        self.prev_week_button.bind(on_press=self._on_prev_week)
        self.week_navigator_container.add_widget(self.prev_week_button)
        
        self.week_label = Label(
            text=f"Week {self._get_week_nr()} {self._get_year()}",
            size_hint=(1, None),
            height=SIZE.HEADER_HEIGHT,
            pos_hint={"center_y": 0.5},
            font_size=FONT.DEFAULT,
            bold=True,
            color=COL.TEXT,
        )
        self.week_navigator_container.add_widget(self.week_label)
        
        self.next_week_button = SettingsButton(
            text=">",
            width=0.4,
            symbol=True,
            color_state=STATE.ACTIVE,
            color=COL.TEXT,
            bg_color=COL.TASK_SELECTED,
        )
        self.next_week_button.bind(on_press=self._on_next_week)
        self.week_navigator_container.add_widget(self.next_week_button)

        self.day_navigator_container = NavigatorContainer()
        self.add_widget(self.day_navigator_container)

        self._setup_day_labels()
        
        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _on_prev_week(self, instance) -> None:
        """Handle previous week button click."""
        from datetime import timedelta
        if self.current_week_start:
            new_week_start = self.current_week_start - timedelta(days=7)
            self._update_week_display(new_week_start)
    
    def _on_next_week(self, instance) -> None:
        """Handle next week button click."""
        from datetime import timedelta
        if self.current_week_start:
            new_week_start = self.current_week_start + timedelta(days=7)
            self._update_week_display(new_week_start)
    
    def _update_week_display(self, week_start) -> None:
        """Update the week display to show the specified week."""
        from datetime import datetime, timedelta
        
        self.current_week_start = week_start
        
        # Update week label
        week_number = week_start.isocalendar()[1]
        year = week_start.year
        self.week_label.text = f"Week {week_number} {year}"
        
        # Update day labels
        self._setup_day_labels_for_week(week_start)
    
    def _setup_day_labels_for_week(self, week_start) -> None:
        """Sets up the day labels for a specific week."""
        from datetime import datetime, timedelta
        
        # Get the current date and selected date (always the task_group date)
        current_date = datetime.now().date()
        selected_date = datetime.strptime(self.task_group.date_str, DM.DATE.DATE_KEY).date()
        
        # Clear existing day labels
        self.day_navigator_container.clear_widgets()
        
        # Generate day labels for the week
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_key = day_date.isoformat()
            
            # Check if this day has tasks
            has_tasks = any(task_group.date_str == day_key for task_group in self.task_manager.task_groups)
            
            # Create day label
            day_label = DateTimeLabel(
                text=str(day_date.day),
                markup=True,
            )
            
            # Set current day highlight FIRST
            if day_date == current_date:
                day_label.set_current_day(True)
            
            # Set selected day highlight SECOND
            if day_date == selected_date:
                day_label.set_selected(True)
            
            # Set text color and styling LAST (after all other styling)
            if has_tasks:
                day_label.color = COL.TEXT
                day_label.font_size += 3
                # Make clickable only if it has tasks
                day_label.bind(on_press=lambda instance, date=day_date: self._on_day_click(date))
            else:
                day_label.color = COL.TEXT_GREY
                day_label.font_size -= 3
            
            self.day_navigator_container.add_widget(day_label)
    
    def _on_day_click(self, day_date) -> None:
        """Handle day button click."""
        logger.info(f"Clicked day: {day_date}")
        
        # Find the task group for this day
        day_key = day_date.isoformat()
        clicked_task_group = None
        
        for task_group in self.task_manager.task_groups:
            if task_group.date_str == day_key:
                clicked_task_group = task_group
                break
        
        # Call refresh_home_screen with the found task group
        home_screen = self._find_home_screen()
        home_screen.current_task_group = clicked_task_group
        if home_screen:
            home_screen.refresh_home_screen()
        else:
            logger.error("Could not find HomeScreen for day click")
    
    def _find_home_screen(self) -> "HomeScreen | None":
        """Finds the HomeScreen by traversing up the widget hierarchy."""
        current = self
        while current:
            if hasattr(current, "name") and current.name == DM.SCREEN.HOME:
                return current
            current = current.parent
        return None
    
    def _setup_day_labels(self) -> None:
        """Sets up the day labels with proper styling based on task availability and current/selected state."""
        from datetime import datetime, timedelta
        
        # Get the current date and selected date (always the task_group date)
        current_date = datetime.now().date()
        selected_date = datetime.strptime(self.task_group.date_str, DM.DATE.DATE_KEY).date()
        
        # Find the start of the week (Monday)
        # isoweekday() returns Monday=1, Tuesday=2, ..., Sunday=7
        days_since_monday = selected_date.isoweekday() - 1
        week_start = selected_date - timedelta(days=days_since_monday)
        
        # Store the current week start for navigation
        self.current_week_start = week_start
        
        logger.info(f"Current date: {current_date}, Selected date: {selected_date}, Week start: {week_start}")
        
        # Use the new method to set up day labels
        self._setup_day_labels_for_week(week_start)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _get_week_nr(self) -> int:
        """Returns the week number of the task group."""
        from datetime import datetime
        # Get the date from the task group's first task
        if self.task_group.tasks:
            task_date = datetime.strptime(self.task_group.date_str, DM.DATE.DATE_KEY).date()
            return task_date.isocalendar()[1]  # ISO week number
        return datetime.now().isocalendar()[1]
    
    def _get_year(self) -> int:
        """Returns the year of the task group."""
        from datetime import datetime
        if self.task_group.tasks:
            task_date = datetime.strptime(self.task_group.date_str, DM.DATE.DATE_KEY).date()
            return task_date.year
        return datetime.now().year
    
    def _get_days(self) -> list[int]:
        """Returns the days of the week as integers."""
        from datetime import datetime, timedelta
        # Get the date from the task group's first task
        if self.task_group.tasks:
            task_date = datetime.strptime(self.task_group.date_str, DM.DATE.DATE_KEY).date()
        else:
            task_date = datetime.now().date()
        
        # Find the start of the week (Monday)
        days_since_monday = task_date.weekday()
        week_start = task_date - timedelta(days=days_since_monday)
        
        # Generate all 7 days of the week
        week_days = []
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            week_days.append(day_date.day)
        
        return week_days


class TaskGroupWidget(BoxLayout):
    """
    A TaskGroupWidget is a container for a TaskGroup.
    TaskGroupWidget
      |-- TaskGroupHeader   [Label]
      |-- TaskInfoContainer [BoxLayout]
          |-- TaskInfo      [Label][background]
          |-- ...
    """
    def __init__(self, task_group: "TaskGroup", **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            **kwargs
        )
        self.task_group: "TaskGroup" = task_group
        self.tasks: list["Task"] = task_group.tasks

        header_text = TaskGroup.get_task_group_header_text(task_group.date_str)
        self.header = TaskGroupHeader(text=header_text)
        self.add_widget(self.header)

        self.task_info_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=0,
        )
        self.add_widget(self.task_info_container)
        
        self.task_info_container.bind(minimum_height=self.task_info_container.setter("height"))
        self.task_info_container.bind(height=self._update_height)
        
        self._add_tasks()
    
    def _add_tasks(self) -> None:
        """Adds all Tasks to the TaskInfoContainer."""
        for i, task in enumerate(self.tasks):
            # First and last for padding purposes
            is_first_task = i == 0
            is_last_task = i == len(self.tasks) - 1
            self._add_task_info(task, is_first_task, is_last_task)
    
    def _update_height(self, instance, value: float) -> None:
        """Updates the height of the TaskGroupWidget by summing the children's heights."""
        self.height = sum(child.height for child in self.children)
    
    def _add_task_info(self, task: "Task",
                       is_first_task: bool, is_last_task: bool) -> None:
        """
        Adds a TaskInfoLabel to the TaskInfoContainer.
        """
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
                                        task=task,
                                        expired=expired,
                                        is_first_task=is_first_task,
                                        is_last_task=is_last_task,
                                       )
        self.task_info_container.add_widget(task_info_label)


class TaskInfoLabel(Label):
    """
    A TaskInfoLabel is a label for displaying task info.
    Contains formatted time, snooze time and message.
    """
    def __init__(self, text: str, task: "Task" = None, expired: bool = False,
                 is_first_task: bool = False, is_last_task: bool = False, **kwargs):
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

        self.task: "Task" = task
        self.task_id: str = str(task.task_id) if task else None
        self.selected: bool = False
        self.is_first_task: bool = is_first_task  # For padding
        self.is_last_task: bool = is_last_task    # For padding

        self.bind(width=self._update_text_size)
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
        
        self.set_expired(expired)  # Sets bg color

    def _update_text_size(self, instance, value: float) -> None:
        """Updates text_size when width changes to enable proper text wrapping."""
        if self.width > 0:
            self.text_size = (self.width, None)

    def _update_height(self, instance, value: float) -> None:
        """Updates the widget height based on the texture size."""
        if self.texture_size[1] > 0:
            self.height = self.texture_size[1]

    def _update_bg(self, instance, value: float) -> None:
        """Updates the background size of the TaskContainer."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_expired(self, expired: bool = True) -> None:
        """Sets the background color based on expired state."""
        if expired:
            self.bg_color.rgba = COL.TASK_INACTIVE
        else:
            self.bg_color.rgba = COL.TASK_ACTIVE
    
    def set_selected(self, selected: bool = True) -> None:
        """Sets the background color based on selected state."""
        self.selected = selected
        if selected:
            self.bg_color.rgba = COL.TASK_SELECTED
        else:
            # When deselecting, check Task expiry state
            if self.task and self.task.expired:
                self.bg_color.rgba = COL.TASK_INACTIVE
            else:
                self.bg_color.rgba = COL.TASK_ACTIVE
    
    def on_touch_down(self, touch) -> None:
        """Handles the touch down event."""
        if not self.collide_point(*touch.pos) or not self.task_id:
            return super().on_touch_down(touch)
        
        home_screen = self._find_home_screen()
        if not home_screen:
            logger.error("Could not find HomeScreen for Task selection")
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
    
    def _find_home_screen(self) -> "HomeScreen | None":
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
    def __init__(self, expired: bool, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))
        
        with self.canvas.before:
            self.bg_color = Color(*COL.FIELD_INPUT)  # Active by default
            self.bg_rect = Rectangle(
                pos=self.pos,
                size=self.size
            )
            self.bind(pos=self._update_bg, size=self._update_bg)
        
        self.set_expired(expired)

    def _update_bg(self, instance, value: float) -> None:
        """Updates the background size of the TaskContainer."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_expired(self, expired: bool = True) -> None:
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
    
    def set_text(self, text: str) -> None:
        self.text = text
