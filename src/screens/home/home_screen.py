import time

from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen

from .home_widgets import EditTaskButton
from .home_screen_utils import HomeScreenUtils
from src.utils.logger import logger
from src.utils.misc import is_widget_visible
from src.settings import SCREEN

if TYPE_CHECKING:
    from src.widgets.buttons import EditTaskButton
    from src.widgets.labels import TaskHeader, TaskLabel, TimeLabel


class HomeScreen(BaseScreen, HomeScreenUtils):
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
        self.task_manager.bind(on_task_saved=self.scroll_to_new_task)
        self.task_manager.bind(on_tasks_changed=self.update_task_display)

        # Can navigate to NewTaskScreen
        self.new_task_screen_ready: bool = False
        # Task attributes
        self.tasks_loaded: bool = False
        self.show_hints: bool = True
        # Edit/delete attributes
        self.edit_delete_visible: bool = False
        self.edit_delete_buttons: list[EditTaskButton] = []
        # Scroll to Task attributes
        self.task_header_widget: TaskHeader | None = None
        self.time_label_widget: TimeLabel | None = None
        self.task_message_widget: TaskLabel | None = None
        
        # Cache for TasksByDate widgets
        self.widget_cache = {}

        # TopBar
        top_left_callback = lambda instance: self.toggle_edit_delete(instance)
        top_bar_callback = lambda instance: self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
        self.top_bar.make_home_bar(top_left_callback=top_left_callback, top_bar_callback=top_bar_callback)
        # TopBarExpanded
        self.top_bar_expanded.make_home_bar(top_left_callback=top_left_callback)

        # BottomBar
        self.add_bottom_bar()
    
    def navigate_to_new_task_screen(self, *args) -> None:
        """
        Navigate to the NewTaskScreen.
        If the edit/delete icons are visible, toggle them off first.
        """
        if not self.new_task_screen_ready:
            logger.error("NewTaskScreen not ready - cannot navigate to it")
            return
        
        if self.edit_delete_visible:
            self.toggle_edit_delete()
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)

    def find_task(self, instance, task) -> None:
        """
        Scroll to a specific Task that was created or edited and highlight its message.
        """
        selected_task_group = self.get_task_group(task)
        if not selected_task_group:
            return False
        
        # Save the Task header
        self.task_header_widget = selected_task_group.children[1]

        # Find message container
        # Save time widget if found
        task_container = self.get_task_container(selected_task_group, task)
        if not task_container or not self.task_header_widget:
            return False
        
        # Save the Task message
        self.task_message_widget = self.get_task_message_widget(task_container)
        if not self.task_message_widget:
            return False
            
        return True

    def scroll_to_new_task(self, instance, task):
        """Scroll to the new/edited task"""
        # Mark to invalidate this Widgets cache
        self.invalidate_cache_for_date = task.get_date_str()
        
        # Set widget attributes
        if not self.find_task(instance, task):
            logger.error(f"No task found - cannot scroll to it")
            return

        # If both the header and message are already visible, just highlight the message
        if (self.task_header_widget is not None and 
            self.task_message_widget is not None and
            is_widget_visible(self.task_message_widget, self.scroll_container.scroll_view)):
            # Task is already visible, just highlight it
            selected_task = self.task_message_widget
            Clock.schedule_once(lambda dt: selected_task.set_active(True), 0.1)
            Clock.schedule_once(lambda dt: selected_task.set_active(False), 3.2)
            Clock.schedule_once(lambda dt: self.clear_go_to_task_references(), 3.3)
            return

        # If not visible, proceed with original scrolling logic
        # Start at the bottom
        self.scroll_container.scroll_view.scroll_y = 0.0

        # Scroll up to Task header
        if self.task_header_widget is not None:
            selected_task_header = self.task_header_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task_header, animate=False), 0.1)

        # Scroll down to task message if not yet in screen
        if self.task_message_widget is not None:
            selected_task = self.task_message_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task, animate=False), 0.15)
            Clock.schedule_once(lambda dt: selected_task.set_active(True), 0.4)
            Clock.schedule_once(lambda dt: selected_task.set_active(False), 3.5)
            Clock.schedule_once(lambda dt: self.clear_go_to_task_references(), 3.6)

    def on_enter(self) -> None:
        super().on_enter()
        # Connect our initial_scroll flag to the scroll container
        self.scroll_container.initial_scroll = self.initial_scroll
        
        if not self.tasks_loaded:
            self.scroll_container.scroll_view.scroll_y = 1.0
            self.tasks_loaded = True
            logger.warning(f"Going to first active task")
        
    
    def on_pre_enter(self) -> None:
        super().on_pre_enter()  # This already handles bottom bar reset
        
        if not hasattr(self, "on_enter_time"):
            on_enter_time = time.time()
            self.on_enter_time = on_enter_time
        
        self.task_manager.set_expired_tasks()

        if not self.tasks_loaded:
            self.update_task_display()
    
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
