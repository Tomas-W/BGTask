import time

from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.animation import Animation

from src.screens.base.base_screen import BaseScreen

from .home_screen_utils import HomeScreenUtils
from src.utils.logger import logger
from src.settings import SCREEN, LOADED, COL, SIZE, SPACE, FONT

if TYPE_CHECKING:
    from src.widgets.labels import TaskHeader, TaskLabel, TimeLabel
    from src.managers.tasks.task_manager_utils import Task


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
        self.task_manager.bind(on_tasks_changed=self.handle_tasks_changed)

        # Task attributes
        self.tasks_loaded: bool = False
        self.show_hints: bool = True
        # Scroll to Task attributes
        self.task_header_widget: TaskHeader | None = None
        self.time_label_widget: TimeLabel | None = None
        self.task_message_widget: TaskLabel | None = None
        
        # Task selection
        self.selected_task: Task | None = None
        self.selected_label: TaskLabel | None = None
        
        # Cache for TasksByDate widgets
        self.widget_cache = {}

        # TopBar
        top_left_callback = lambda instance: self.toggle_edit_delete(instance)
        top_bar_callback = self.navigate_to_new_task_screen
        self.top_bar.make_home_bar(top_left_callback=top_left_callback, top_bar_callback=top_bar_callback)
        # TopBarExpanded
        self.top_bar_expanded.make_home_bar(top_left_callback=top_left_callback)

        # Floating action buttons
        self.create_floating_action_buttons()
        
        # BottomBar
        self.add_bottom_bar()
    
    def create_floating_action_buttons(self):
        """Create floating edit/delete buttons that appear when a task is selected"""
        # Create a container for the buttons
        self.floating_button_container = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=SIZE.BUTTON_HEIGHT,
            width=SIZE.BUTTON_WIDTH * 2 + SPACE.SPACE_M if hasattr(SIZE, "BUTTON_WIDTH") else dp(200),
            pos_hint={"center_x": 0.5, "y": 0.1},  # Position near bottom
            spacing=SPACE.SPACE_M,
            opacity=0  # Hidden by default
        )
        
        # Edit button
        self.edit_button = Button(
            text="Edit",
            size_hint=(1, 1),
            color=COL.TEXT,
            font_size=FONT.BUTTON,
            background_color=COL.FIELD_PASSED
        )
        self.edit_button.bind(on_release=self.edit_selected_task)
        
        # Delete button
        self.delete_button = Button(
            text="Delete",
            size_hint=(1, 1),
            color=COL.TEXT,
            font_size=FONT.BUTTON,
            background_color=COL.ERROR
        )
        self.delete_button.bind(on_release=self.delete_selected_task)
        
        # Add buttons to container
        self.floating_button_container.add_widget(self.edit_button)
        self.floating_button_container.add_widget(self.delete_button)
        
        # Add container to the screen
        self.add_widget(self.floating_button_container)
    
    def select_task(self, task, label=None):
        """Select a task and show floating action buttons"""
        # Deselect previous task if any
        if self.selected_label:
            self.selected_label.set_selected(False)
        
        # If selecting the same task, deselect it
        if self.selected_task and self.selected_task.task_id == task.task_id:
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
            return
        
        # Select new task
        self.selected_task = task
        
        # Store and update the label
        if label:
            self.selected_label = label
            label.set_selected(True)
        
        # Show floating buttons
        self.show_floating_buttons()
    
    def show_floating_buttons(self):
        """Show floating action buttons with animation"""
        self.floating_button_container.opacity = 0
        self.floating_button_container.pos_hint = {"center_x": 0.5, "y": 0.05}
        animation = Animation(opacity=1, pos_hint={"center_x": 0.5, "y": 0.1}, duration=0.3)
        animation.start(self.floating_button_container)
    
    def hide_floating_buttons(self):
        """Hide floating action buttons with animation"""
        animation = Animation(opacity=0, pos_hint={"center_x": 0.5, "y": 0.05}, duration=0.3)
        animation.start(self.floating_button_container)
    
    def edit_selected_task(self, instance):
        """Edit the currently selected task"""
        if self.selected_task:
            task_id = str(self.selected_task.task_id)  # Ensure it's a string
            # Log the task ID we're trying to edit
            logger.debug(f"Attempting to edit task with ID: {task_id}")
            
            # Get a fresh reference to the task to avoid stale data
            fresh_task = self.task_manager.get_task_by_id(task_id)
            if fresh_task:
                # Store reference to task for efficiency
                self.edited_task = fresh_task
                
                # CRITICAL: First dispatch event from task_manager to load task data in the NewTaskScreen
                self.task_manager.dispatch("on_task_edit", task=fresh_task)
                
                # THEN navigate to the edit screen after the data is loaded
                Clock.schedule_once(lambda dt: self.navigation_manager.navigate_to(SCREEN.NEW_TASK), 0.1)
            else:
                logger.error(f"Failed to edit task: Task with ID {task_id} not found")
                # Refresh the UI to sync with current task state
                self.update_task_display()
                
            # Clean up selection state
            if self.selected_label:
                self.selected_label.set_selected(False)
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
    
    def delete_selected_task(self, instance):
        """Delete the currently selected task"""
        if self.selected_task:
            task_id = str(self.selected_task.task_id)  # Ensure it's a string
            logger.debug(f"Attempting to delete task with ID: {task_id}")
            
            # Get a fresh reference to the task to avoid stale data
            fresh_task = self.task_manager.get_task_by_id(task_id)
            if fresh_task:
                # Clear selection before deletion to prevent selection restore attempts
                if self.selected_label:
                    self.selected_label.set_selected(False)
                self.selected_task = None
                self.selected_label = None
                self.hide_floating_buttons()
                
                # Now delete the task
                self.task_manager.delete_task(task_id)
                # TaskManager will handle triggering update_task_display with the modified task
            else:
                logger.error(f"Failed to delete task: Task with ID {task_id} not found")
                # Refresh the UI to sync with current task state
                self.update_task_display()
                
                # Clean up selection state (if we got here due to error)
                if self.selected_label:
                    self.selected_label.set_selected(False)
                self.selected_task = None
                self.selected_label = None
                self.hide_floating_buttons()
    
    def navigate_to_new_task_screen(self, *args) -> None:
        """
        Navigate to the NewTaskScreen.
        If the edit/delete icons are visible, toggle them off first.
        Also deselect any selected task.
        """
        if not LOADED.NEW_TASK:
            logger.error("NewTaskScreen not ready - cannot navigate to it")
            return
        
        # Deselect any selected task
        if self.selected_task:
            if self.selected_label:
                self.selected_label.set_selected(False)
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
        
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
        
        self.scroll_container.scroll_view.scroll_y = 1.0

        # Scroll up to Task header
        if self.task_header_widget is not None:
            selected_task_header = self.task_header_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task_header, animate=False), 0.2)

        # Scroll down to task message if not yet in screen
        if self.task_message_widget is not None:
            selected_task = self.task_message_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(selected_task, animate=False), 0.25)
            Clock.schedule_once(lambda dt: selected_task.set_active(True), 0.3)
            Clock.schedule_once(lambda dt: selected_task.set_active(False), 4)
            Clock.schedule_once(lambda dt: self.clear_go_to_task_references(), 4.1)
    
    def on_pre_enter(self) -> None:
        super().on_pre_enter()
        
        if not hasattr(self, "on_enter_time"):
            on_enter_time = time.time()
            self.on_enter_time = on_enter_time
        
        self.task_manager.set_expired_tasks()

        # Fallback
        if not self.tasks_loaded:
            self._full_rebuild_task_display()

    def on_enter(self) -> None:
        super().on_enter()
        # Connect our initial_scroll flag to the scroll container
        self.scroll_container.initial_scroll = self.initial_scroll
        
        if not self.tasks_loaded:
            self.scroll_container.scroll_view.scroll_y = 1.0
            self.tasks_loaded = True
            logger.warning(f"Going to first active task")
    
    def on_leave(self):
        """Handle screen exit - deselect any task"""
        super().on_leave()
        
        # Deselect any selected task
        if self.selected_task:
            if self.selected_label:
                self.selected_label.set_selected(False)
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
    
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

    def handle_tasks_changed(self, instance, **kwargs):
        """Handle the on_tasks_changed event with potential modified_task parameter"""
        modified_task = kwargs.get("modified_task")
        logger.debug(f"Handling tasks_changed event, modified_task: {modified_task.task_id if modified_task else None}")
        self.update_task_display(modified_task=modified_task)
