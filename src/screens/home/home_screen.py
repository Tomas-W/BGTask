import time

from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen

from .home_widgets import TasksByDate
from src.widgets.containers import ScrollContainer

from src.utils.logger import logger

from src.settings import SCREEN, SIZE, SPACE

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
        self.task_manager.bind(on_tasks_changed=self.update_task_display)

        # Task attributes
        self.tasks_loaded: bool = False
        self.show_hints: bool = True
        # Edit/delete attributes
        self.edit_delete_visible: bool = False
        self.edit_delete_buttons: list[EditTaskButton] = []
        
        # Top bar
        top_left_callback = lambda instance: self.toggle_edit_delete(instance)
        top_bar_callback = lambda instance: self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
        self.top_bar.make_home_bar(top_left_callback=top_left_callback, top_bar_callback=top_bar_callback)
        # Top bar expanded
        self.top_bar_expanded.make_home_bar(top_left_callback=top_left_callback)

        # Scroll container
        self.scroll_container = ScrollContainer()
        
        # Apply layout
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        # Add bottom bar
        self.add_bottom_bar()
        # Apply layout
        self.add_widget(self.root_layout)
    
    def test_callback(self, *args) -> None:
        """Test callback for the edit button"""
        logger.debug("test_callback")

    def navigate_to_new_task(self, *args) -> None:
        """
        Navigate to the NewTaskScreen.
        If the edit/delete icons are visible, toggle them off first.
        """
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
        """Toggle the visibility state of the edit and delete buttons."""
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
    
    def update_task_display(self, *args) -> None:
        """
        Rebuild the Task widgets by clearing the existing widgets and
         creating new ones.
        """
        # Clear widgets
        self.scroll_container.clear_widgets()
        self.edit_delete_buttons = []
        self.tasks_by_dates = []

        # Create new widgets
        for group in self.task_manager.get_tasks_by_dates():
            task_group = TasksByDate(
                date_str=group["date"],
                tasks=group["tasks"],
                task_manager=self.task_manager,
                parent_screen=self,
                size_hint=(1, None)
            )
            self.scroll_container.add_widget_to_container(task_group)
            self.tasks_by_dates.append(task_group)
        
        self.check_for_edit_delete()
        logger.debug(f"Updated task display")
    
    def register_edit_delete_button(self, button: "EditTaskButton") -> None:
        """Register an edit/delete button with this screen"""
        self.edit_delete_buttons.append(button)
    
    def on_pre_enter(self) -> None:
        super().on_pre_enter()
        if not hasattr(self, "on_enter_time"):
            on_enter_time = time.time()
            self.on_enter_time = on_enter_time
        
        if not self.tasks_loaded:
            self.update_task_display()
            self.tasks_loaded = True
        
        self.task_manager.set_expired_tasks()
        self.update_task_display()
        
        # Scroll down and then to the first active task
        self.scroll_container.scroll_view.scroll_y = 0.0
        Clock.schedule_once(self.scroll_to_first_active_task, 0.1)

    def scroll_to_first_active_task(self, dt):
        """
        Scrolls to show the first non-expired task at the top of the view.
        Works consistently across different screen sizes.
        """
        if not self.tasks_by_dates:
            return
        
        for task_group in self.tasks_by_dates:
            if not task_group.all_expired:
                self.scroll_container.scroll_view.scroll_to(task_group)
                return
        return