import time

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from src.screens.home.home_widgets import TaskGroupWidget, TaskNavigator

from managers.tasks.task import Task, TaskGroup
from managers.device.device_manager import DM

from src.utils.wrappers import disable_gc
from src.utils.logger import logger
from src.settings import COL, FONT, SIZE, SPACE

if TYPE_CHECKING:
    from src.screens.home.home_widgets import TaskInfoLabel


class HomeScreenUtils:
    """
    Utility class for the HomeScreen.
    """
    def __init__(self):
        pass
    
# ########## REFRESHING ########## #
    def _init_home_screen(self, *args) -> None:
        """
        Displays the current TaskGroup or else creates and displays the welcome TaskGroup.
        """
        start_time = time.time()
        task_group = self.task_manager.get_current_task_group()
        # No current TaskGroup, create welcome TaskGroup and recall
        if task_group is None:
            self._set_welcome_task_group()
            self._init_home_screen()
            return

        self.scroll_container.container.clear_widgets()
        task_group_widget = TaskGroupWidget(task_group=task_group)
        self.scroll_container.container.add_widget(task_group_widget)
        
        logger.info(f"Refreshing HomeScreen took: {round(time.time() - start_time, 6)} seconds")
    
    @disable_gc
    def refresh_home_screen(self, *args) -> None:
        """
        Rebuilds the HomeScreen UI based on the current TaskGroup.
        Also refreshes the WallpaperScreen.
        If no TaskGroup is set, it will get the nearest future TaskGroup or welcome TaskGroup.
        """
        start_time = time.time()

        self.deselect_task()
        
        # Update TaskNavigator
        self.layout.remove_widget(self.task_navigator)
        self.task_navigator = TaskNavigator(task_group=self.task_manager.current_task_group, task_manager=self.task_manager)
        self.layout.add_widget(self.task_navigator, index=1)
        
        # Update TaskGroupWidget
        self.scroll_container.container.clear_widgets()
        task_group_widget = TaskGroupWidget(task_group=self.task_manager.current_task_group)
        self.scroll_container.container.add_widget(task_group_widget)

        # Refresh WallpaperScreen
        self.app.get_screen(DM.SCREEN.WALLPAPER).refresh_wallpaper_screen()
        
        logger.info(f"Refreshing HomeScreen took: {round(time.time() - start_time, 6)} seconds")
    
# ########## SELECTING ########## #
    def select_task(self, task: Task, label: "TaskInfoLabel" = None) -> None:
        """Selects a Task and shows the floating action buttons."""
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
    
    def edit_selected_task(self, instance) -> None:
        """Navigates to the NewTaskScreen to edit the currently selected Task."""
        if self.selected_task:
            task_id = str(self.selected_task.task_id)
            task_to_edit = self.task_manager.get_task_by_id_(task_id)
            if task_to_edit:
                self.app.get_screen(DM.SCREEN.NEW_TASK).load_task_data(task=task_to_edit)
                Clock.schedule_once(lambda dt: self.navigation_manager.navigate_to(DM.SCREEN.NEW_TASK), 0.1)
            else:
                logger.error(f"Error editing Task: {DM.get_task_id_log(task_id)} not found")

            # Clean up selection state
            if self.selected_label:
                self.selected_label.set_selected(False)
            
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
    
    def delete_selected_task(self, instance=None) -> None:
        """Deletes the currently selected Task."""
        if self.selected_task:
            task_id = str(self.selected_task.task_id) 
            task_to_delete = self.task_manager.get_task_by_id_(task_id)
            if task_to_delete:
                # Remove selection
                if self.selected_label:
                    self.selected_label.set_selected(False)
                
                # Delete references
                self.selected_task = None
                self.selected_label = None
                self.hide_floating_buttons()
                # Delete Task
                self.task_manager.delete_task(task_id)
            else:
                logger.error(f"Error deleting Task: {DM.get_task_id_log(task_id)} not found")
                self.refresh_home_screen()
                
                # Clean up selection state
                if self.selected_label:
                    self.selected_label.set_selected(False)
                
                self.selected_task = None
                self.selected_label = None
                self.hide_floating_buttons()
    
    def deselect_task(self) -> None:
        """Deselects the currently selected Task."""
        if self.selected_label:
            self.selected_label.set_selected(False)
        self.selected_task = None
        self.selected_label = None
        self.hide_floating_buttons()
    
    def _highlight_task(self, task_widget: "TaskInfoLabel", *args) -> None:
        """Highlights the Task."""
        if task_widget is not None:
            task_widget.set_active(True)

    def _unhighlight_task(self, task_widget: "TaskInfoLabel", *args) -> None:
        """Unhighlights the Task."""
        if task_widget is not None:
            task_widget.set_active(False)
    
    def create_floating_action_buttons(self) -> None:
        """Creates floating edit/delete buttons that appear when a Task is selected."""
        # Container for the buttons
        self.floating_button_container = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=SIZE.FLOATING_CONTAINER_HEIGHT,
            width=SIZE.FLOATING_CONTAINER_WIDTH,
            pos_hint={"center_x": 0.5, "y": 0.1},  # Position near bottom
            spacing=SPACE.SPACE_M,
            opacity=0                              # Hidden by default
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
        
    def show_floating_buttons(self) -> None:
        """Shows the floating action buttons with animation."""
        self.floating_button_container.opacity = 0
        self.floating_button_container.pos_hint = {"center_x": 0.5, "y": 0.05}
        animation = Animation(opacity=1, pos_hint={"center_x": 0.5, "y": 0.1}, duration=0.3)
        animation.start(self.floating_button_container)
    
    def hide_floating_buttons(self) -> None:
        """Hides the floating action buttons with animation."""
        animation = Animation(opacity=0, pos_hint={"center_x": 0.5, "y": 0.05}, duration=0.3)
        animation.start(self.floating_button_container)
