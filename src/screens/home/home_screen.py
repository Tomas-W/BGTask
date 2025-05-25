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
    from src.screens.home.home_widgets import TaskHeader, TaskLabel, TimeLabel
    from managers.tasks.task_manager_utils import Task


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
        self.task_manager.bind(on_task_saved_scroll_to_task=self.scroll_to_task)
        self.task_manager.bind(
            on_tasks_changed_update_task_display=lambda instance,
             **kwargs: self.update_task_display(modified_task=kwargs.get("modified_task")))
        self.task_manager.bind(
            on_tasks_expired_set_date_expired=self.set_date_expired)
        self.task_manager.bind(
            on_task_cancelled_update_ui=self.update_task_display)

        # Loading attributes
        self.tasks_loaded: bool = False
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
        top_bar_callback = self.navigate_to_new_task_screen
        top_left_callback = lambda instance: self.navigation_manager.navigate_to(SCREEN.START)
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
            task_id = str(self.selected_task.task_id)
            task_to_edit = self.task_manager.get_task_by_id(task_id)
            if task_to_edit:
                self.task_manager.dispatch("on_task_edit_load_task_data", task=task_to_edit)
                Clock.schedule_once(lambda dt: self.navigation_manager.navigate_to(SCREEN.NEW_TASK), 0.1)
            else:
                logger.error(f"Failed to edit task: Task with ID {task_id} not found")
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
            task_id = str(self.selected_task.task_id) 
            task_to_delete = self.task_manager.get_task_by_id(task_id)
            if task_to_delete:
                # Remove selection
                if self.selected_label:
                    self.selected_label.set_selected(False)
                # Delete references
                self.selected_task = None
                self.selected_label = None
                self.hide_floating_buttons()
                
                # Now delete the task
                self.task_manager.delete_task(task_id)
            else:
                logger.error(f"Failed to delete task: Task with ID {task_id} not found")
                self.update_task_display()
                
                # Clean up selection state
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

    def scroll_to_task(self, instance, task, *args, **kwargs):
        """Scroll to the new/edited task"""
        # Mark to invalidate this Widgets cache
        task = kwargs.get("task") if kwargs.get("task") else task
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

    def set_date_expired(self, instance, date):
        """
        Sets background color of given date's TaskGroup to inactive.
        """   
        # Find the task group widget for this date
        for task_group in self.active_task_widgets:
            # The task_group.date_str is already formatted like "Today, April 10"
            # while the date from task_manager might be in raw format like "Thursday 10 Apr"
            from src.utils.misc import get_task_header_text
            if task_group.date_str == date or task_group.date_str == get_task_header_text(date):
                # Update the appearance - this just changes the background color
                if not task_group.all_expired:
                    task_group.tasks_container.set_expired(True)
                    task_group.all_expired = True
                    logger.debug(f"Date expired: {date}")
                break
