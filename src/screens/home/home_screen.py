import time

from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen

from .home_widgets import TasksByDate, TaskContainer, TimeContainer, TimeLabel, TaskLabel
from src.widgets.containers import ScrollContainer

from src.widgets.misc import Spacer

from src.utils.logger import logger

from src.settings import SCREEN, SIZE, COL

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
        self.task_manager.bind(on_task_saved=self.scroll_to_new_task)
        self.task_manager.bind(on_tasks_changed=self.update_task_display)

        # Task attributes
        self.tasks_loaded: bool = False
        self.show_hints: bool = True
        # Edit/delete attributes
        self.edit_delete_visible: bool = False
        self.edit_delete_buttons: list[EditTaskButton] = []
        # Scroll to Task attributes
        self.task_header_widget = None
        self.time_label_widget = None
        self.task_message_widget = None

        # Top bar
        top_left_callback = lambda instance: self.toggle_edit_delete(instance)
        top_bar_callback = lambda instance: self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
        self.top_bar.make_home_bar(top_left_callback=top_left_callback, top_bar_callback=top_bar_callback)
        # Top bar expanded
        self.top_bar_expanded.make_home_bar(top_left_callback=top_left_callback)

        # Scroll container
        self.scroll_container = ScrollContainer(scroll_callback=self.check_for_bottom_spacer)
        self.scroll_container.main_self = self
        # Apply layout
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        # Add bottom bar
        self.add_bottom_bar()
        # Apply layout
        self.add_widget(self.root_layout)

        self.bottom_spacer = Spacer(height=SIZE.BOTTOM_BAR_HEIGHT, color=COL.BG)

    def navigate_to_new_task(self, *args) -> None:
        """
        Navigate to the NewTaskScreen.
        If the edit/delete icons are visible, toggle them off first.
        """
        if self.edit_delete_visible:
            self.toggle_edit_delete()
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
    def check_for_bottom_spacer(self, *args) -> None:
        """Check if the bottom spacer is in the layout"""
        if self.bottom_bar.visible:
            if not self.bottom_spacer in self.layout.children:
                self.layout.add_widget(self.bottom_spacer)
        else:
            if self.bottom_spacer in self.layout.children:
                self.layout.remove_widget(self.bottom_spacer)
    
    def update_task_display(self, *args) -> None:
        """
        Rebuild the Task widgets by clearing the existing widgets and
         creating new ones.
        """
        # Clear widgets
        self.scroll_container.container.clear_widgets()
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
            self.scroll_container.container.add_widget(task_group)
            self.tasks_by_dates.append(task_group)
        
        # Compensate for the BottomBar
        self.check_for_bottom_spacer()
        
        self.check_for_edit_delete()
        logger.debug(f"Updated task display")
    
    def scroll_to_first_active_task(self, dt):
        """
        Scrolls up to show the first non-expired Task.
        Only used on first enter.
        """
        # Start at the bottom
        self.scroll_container.scroll_view.scroll_y = 0.0
        if not self.tasks_by_dates:
            return
        
        for task_group in self.tasks_by_dates:
            # Always scroll to Today
            if task_group.date_str == "Today":
                Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(task_group, animate=False), 0.2)
                break

            # If no Today, scroll to the first non-expired Task
            if not task_group.all_expired:
                Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(task_group, animate=False), 0.2)
                break
        return

    def get_task_group(self, task) -> TasksByDate:
        """Get the TaskGroup that contains the task"""
        for task_group in self.tasks_by_dates:
            if task in task_group.tasks:
                return task_group
        return None
    
    def get_task_container(self, task_group, task) -> TaskContainer:
        """Get the TaskContainer that contains the task"""
        task_time = task.get_time_str()
        for task_container in task_group.tasks_container.children:
            for child in task_container.children:

                if isinstance(child, TimeContainer):
                    for time_component in child.children:
                        # Confirm time entry & save the Task's container
                        if isinstance(time_component, TimeLabel):
                            if time_component.text == task_time:
                                self.time_label_widget = time_component
                                logger.error(f"Time label widget: {self.time_label_widget}")
                                return task_container
        return None

    def get_task_message_widget(self, task_container) -> TaskLabel:
        """Get the TaskLabel that contains the task message"""
        for child in task_container.children:
            if isinstance(child, TaskLabel):
                self.task_message_widget = child
                logger.error(f"Task message widget: {self.task_message_widget}")
                return child
        return None
    
    def find_task(self, instance, task) -> None:
        """
        Scroll to a specific Task that was saved and highlight its message.
        """
        selected_task_group = self.get_task_group(task)
        if not selected_task_group:
            return False
        
        # Save the Task header
        self.task_header_widget = selected_task_group.children[1]

        # Find message container
        # Save time widget if found
        task_container = self.get_task_container(selected_task_group, task)
        logger.error(f"Task container: {task_container}")
        if not task_container or not self.task_header_widget:
            return False
        
        # Save the Task message
        self.task_message_widget = self.get_task_message_widget(task_container)
        if not self.task_message_widget:
            return False
            
        return True

    def clear_go_to_widget(self):
        """Clear the go to widget attributes"""
        self.task_header_widget = None
        self.time_label_widget = None
        self.task_message_widget = None
    
    def scroll_to_new_task(self, instance, task):
        """Scroll to the new/edited task"""
        # Set widget attributes
        if not self.find_task(instance, task):
            logger.error(f"No task found - cannot scroll to it")
            return

        # Start at the bottom
        self.scroll_container.scroll_view.scroll_y = 0.0

        # Scroll up to Task header
        if self.task_header_widget is not None:
            selected_task_header = self.task_header_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task_header, animate=False), 0.1)

        # Scroll down to task message if not yet in screen
        if self.task_message_widget is not None:
            selected_task = self.task_message_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task, animate=False), 0.25)
            Clock.schedule_once(lambda dt: self.task_message_widget.set_active(True), 0.26)
            Clock.schedule_once(lambda dt: self.task_message_widget.set_active(False), 3)
            Clock.schedule_once(lambda dt: self.clear_go_to_widget(), 3.1)

    def on_enter(self) -> None:
        super().on_enter()
        if not self.tasks_loaded:
            self.scroll_to_first_active_task(None)
            self.tasks_loaded = True
            logger.warning(f"Going to first active task")
    
    def on_pre_enter(self) -> None:
        super().on_pre_enter()
        if not hasattr(self, "on_enter_time"):
            on_enter_time = time.time()
            self.on_enter_time = on_enter_time
        
        if not self.tasks_loaded:
            self.update_task_display()
            self.scroll_container.scroll_view.scroll_y = 1.0
        
        self.task_manager.set_expired_tasks()
    
    def register_edit_delete_button(self, button: "EditTaskButton") -> None:
        """Register an edit/delete button with this screen"""
        self.edit_delete_buttons.append(button)
    
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
