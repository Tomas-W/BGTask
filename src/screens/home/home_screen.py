import time

from datetime import datetime
from typing import TYPE_CHECKING

from kivy.uix.floatlayout import FloatLayout

from src.screens.base.base_screen import BaseScreen  # type: ignore

from .home_widgets import TasksbyDate
from src.widgets.bars import HomeBarClosed, HomeBarExpanded
from src.widgets.buttons import BottomBar
from src.widgets.containers import BaseLayout, ScrollContainer

from src.settings import TEXT, SCREEN

if TYPE_CHECKING:
    from src.widgets.buttons import EditTaskButton


class HomeScreen(BaseScreen):
    """
    HomeScreen is the main screen for the app that:
    - Has a top bar with a settings button, new task button, and exit button
    - Displays a list of tasks grouped by date
    - Has a bottom bar with a scroll to top button
    """
    def __init__(self, navigation_manager, task_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        
        self.show_hints: bool = True
        self.edit_delete_visible: bool = False
        self.edit_delete_buttons: list[EditTaskButton] = []
        
        self.root_layout: FloatLayout = FloatLayout()
        self.layout: BaseLayout = BaseLayout()
        
        # Basic TopBar
        self.top_bar: HomeBarClosed = HomeBarClosed(
            edit_callback=self.toggle_edit_delete,
            new_task_callback=self.navigate_to_new_task,
            options_callback=lambda instance: self.switch_top_bar(),
        )
        # TopBar with expanded options
        self.top_bar_expanded: HomeBarExpanded = HomeBarExpanded(
            edit_callback=self.toggle_edit_delete,
            screenshot_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.START),
            options_callback=lambda instance: self.switch_top_bar(),
            settings_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.SETTINGS),
            exit_callback=self.navigation_manager.exit_app,
        )
        self.layout.add_widget(self.top_bar.top_bar_container)
        
        # Scrollable container for task groups
        self.scroll_container: ScrollContainer = ScrollContainer()
        
        # Bottom bar with ^ button
        self.bottom_bar = BottomBar(text="^")
        self.bottom_bar.bind(on_press=self.scroll_container.scroll_to_top)
        self.scroll_container.connect_bottom_bar(self.bottom_bar)
        
        # Apply layout
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.root_layout.add_widget(self.bottom_bar)
        self.add_widget(self.root_layout)
    
    def navigate_to_new_task(self, *args) -> None:
        if self.edit_delete_visible:
            self.toggle_edit_delete()
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
    def check_for_edit_delete(self) -> None:
        """
        Toggle the visibility of the edit and delete icons based on the current state.
        """
        if self.edit_delete_visible:
            self.show_edit_delete()
        else:
            self.hide_edit_delete()
    
    def toggle_edit_delete(self, *args) -> None:
        """Toggle the visibility state of the edit and delete icons."""
        self.edit_delete_visible = not self.edit_delete_visible
        self.check_for_edit_delete()
    
    def show_edit_delete(self) -> None:
        """Show the edit and delete icons for every Task."""
        for button in self.edit_delete_buttons:
            button.set_opacity(1)
            button.set_disabled(False)
    
    def hide_edit_delete(self) -> None:
        """Hide the edit and delete icons for every Task."""
        for button in self.edit_delete_buttons:
            button.set_opacity(0)
            button.set_disabled(True)

    def load_tasks(self) -> None:
        """Load tasks from the TaskManager and update the task display."""
        self.task_manager.load_tasks()
        self.update_task_display()
    
    def update_task_display(self) -> None:
        """Update the task display widgets."""
        self.scroll_container.clear_widgets()
        
        self.tasks_by_dates = []
        for group in self.task_manager.get_tasks_by_dates()    :
            task_group = TasksbyDate(
                date_str=group["date"],
                tasks=group["tasks"],
                size_hint=(1, None)
            )
            self.scroll_container.add_widget_to_container(task_group)
            self.tasks_by_dates.append(task_group)
        
        self.check_for_edit_delete()
    
    def on_pre_enter(self):
        super().on_pre_enter()
        # Load tasks first
        self.task_manager.load_tasks()
        # Then check if we have any tasks
        if not self.task_manager.tasks and self.show_hints:
            self.task_manager.add_task(message=TEXT.NO_TASKS, timestamp=datetime.now())
            self.show_hints = False
        
        self.update_task_display()
    
    def on_enter(self):
        on_enter_time = time.time()
        self.on_enter_time = on_enter_time