import time

from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen

from .home_widgets import TasksByDate
from src.widgets.containers import ScrollContainer

from src.utils.logger import logger

from src.settings import SCREEN, SIZE

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
        self.task_manager.bind(on_task_saved=self.find_task)
        self.task_manager.bind(on_tasks_changed=self.update_task_display)

        # Task attributes
        self.tasks_loaded: bool = False
        self.show_hints: bool = True
        # Edit/delete attributes
        self.edit_delete_visible: bool = False
        self.edit_delete_buttons: list[EditTaskButton] = []
        # Scroll to task attributes
        self.task_header_widget = None
        self.task_message_widget = None

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

    def navigate_to_new_task(self, *args) -> None:
        """
        Navigate to the NewTaskScreen.
        If the edit/delete icons are visible, toggle them off first.
        """
        if self.edit_delete_visible:
            self.toggle_edit_delete()
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
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
        
        self.check_for_edit_delete()
        logger.debug(f"Updated task display")
    
    def scroll_to_first_active_task(self, dt):
        """
        Scrolls to show the first non-expired task at the top of the view.
        Only used on first enter.
        """
        self.scroll_container.scroll_view.scroll_y = 0.0
        if not self.tasks_by_dates:
            return
        
        for task_group in self.tasks_by_dates:
            if task_group.date_str == "Today":
                Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(task_group, animate=False), 0.2)
                break

            if not task_group.all_expired:
                Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(task_group, animate=False), 0.2)
                break
        return
    
    def find_task(self, instance, task) -> None:
        """
        Scroll to a specific task that was saved and highlight its components.
        """
        from src.screens.home.home_widgets import (TaskLabel, TimeLabel,
                                                   TaskHeader, TimeContainer)
        self.scroll_container.scroll_view.scroll_y = 0.0
        selected_task_group = None
        # Search for the task in the task groups
        for task_group in self.tasks_by_dates:
            logger.error(f"task_group: {task_group}")
            logger.error(f"typeof task_group: {type(task_group)}")
            if task in task_group.tasks:
                selected_task_group = task_group
                break
        
        if not selected_task_group:
            return
        
        # Find and store task header
        # for child in selected_task_group.children:
        #     if isinstance(child, TaskHeader):
        #         self.task_header_widget = child
        #         logger.error(f"Selected day: {self.task_header_widget.text}")
        #         logger.error(f"typeof self.task_header_widget: {type(self.task_header_widget)}")
        #         break
        
        self.task_header_widget = selected_task_group.children[1]

        task_message_widget = None
        selected_time = None
        task_time = task.get_time_str()
        # Confirm time entry
        # Find message container
        for task_container in selected_task_group.tasks_container.children:
            for child in task_container.children:

                if isinstance(child, TimeContainer):
                    for time_component in child.children:

                        if isinstance(time_component, TimeLabel):
                            if time_component.text == task_time:
                                selected_time = time_component.text
                                logger.error(f"Selected time: {selected_time}")
                                logger.error(f"typeof selected_time: {type(selected_time)}")
                                container = task_container
                                break
        
        # Find and store message
        for child in container.children:
            logger.error(f"Child: {child}")
            if isinstance(child, TaskLabel):
                task_message_widget = child
                child.set_active(True)
                logger.error(f"Selected message: {task_message_widget.text}")
                logger.error(f"typeof task_message_widget: {type(task_message_widget)}")
                break
        
        # Confirm task message and time entry
        if task_message_widget and selected_time:
            self.task_message_widget = task_message_widget
    
    def scroll_to_new_task(self):
        """Scroll to the new/edited task"""
        

        # Scroll down to task header
        if self.task_header_widget is not None:
            selected_task_header = self.task_header_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task_header, padding=[0, SIZE.TEST], animate=False), 0.1)
            self.task_header_widget = None

        # Scroll down to task message
        if self.task_message_widget is not None:
            selected_task = self.task_message_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task, padding=[0, SIZE.TEST], animate=False), 0.11)
            self.task_message_widget = None
    
    def on_enter(self) -> None:
        super().on_enter()
        if not self.tasks_loaded:
            self.scroll_to_first_active_task(None)
            self.tasks_loaded = True
            logger.warning(f"Going to first active task")
        
        else:        
            # Scroll to new/edited task
            self.scroll_to_new_task()
    
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
