import time

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from src.screens.home.home_widgets import TaskGroupWidget
from managers.tasks.task import Task, TaskGroup

from managers.device.device_manager import DM

from src.utils.logger import logger
from src.settings import COL, FONT, SIZE, SPACE

if TYPE_CHECKING:
    from src.screens.home.home_widgets import TaskInfoLabel


class HomeScreenUtils:

    FIRST_TASK_MESSAGE = "No upcomming Tasks!\n\nPress + to add a new one,\nor select a Task to edit or delete."

    def __init__(self):
        pass

# ########## REFRESHING ########## #
    def _init_home_screen(self, *args) -> None:
        """
        Initializes the HomeScreen UI.
        Displays the first TaskGroup.
        """
        start_time = time.time()
        # start_group = self.get_start_task_group()
        start_group = self.task_manager.get_current_task_group()
        if start_group is None:
            self._set_first_task_group()
            self._init_home_screen()
            return

        self.scroll_container.container.clear_widgets()
        task_group_widget = TaskGroupWidget(task_group=start_group)
        self.scroll_container.container.add_widget(task_group_widget)
        
        logger.info(f"Refreshing HomeScreen took: {round(time.time() - start_time, 6)} seconds")
    
    def refresh_home_screen(self, *args) -> None:
        """Refreshes task_groups and rebuilds the HomeScreen UI."""
        start_time = time.time()

        self.deselect_task()

        # Use provided task_group if available, otherwise get the start task group
        if self.current_task_group is not None:
            current_task_group = self.current_task_group
        else:
            current_task_group = self.get_start_task_group()
        
        logger.info(f"Current task group: {current_task_group.date_str}")
        
        # Update the existing TaskNavigator with the new task group
        if hasattr(self, 'task_navigator'):
            # Remove the old TaskNavigator
            self.layout.remove_widget(self.task_navigator)
            
            # Create a new TaskNavigator with the updated task group
            from src.screens.home.home_widgets import TaskNavigator
            self.task_navigator = TaskNavigator(task_group=current_task_group, task_manager=self.task_manager)
            self.layout.add_widget(self.task_navigator, index=1)
        
        # Clear and recreate the scroll container content
        self.scroll_container.container.clear_widgets()
        task_group_widget = TaskGroupWidget(task_group=current_task_group)
        self.scroll_container.container.add_widget(task_group_widget)
        
        logger.info(f"Refreshing HomeScreen took: {round(time.time() - start_time, 6)} seconds")
    
    def get_start_task_group(self) -> TaskGroup | None:
        """
        Gets the earliest future TaskGroup (including today).
        Returns None if no future tasks exist.
        """
        if not self.task_manager.task_groups:
            return None
        
        today_key = datetime.now().date().isoformat()
        # Find earliest future TaskGroup
        for task_group in self.task_manager.task_groups:
            if task_group.date_str >= today_key:
                return task_group
        
        return None

    def _set_first_task_group(self) -> None:
        """Sets the first TaskGroup in the TaskManager."""
        first_task = Task(
            message=HomeScreenUtils.FIRST_TASK_MESSAGE,
            timestamp=datetime.now() - timedelta(minutes=1),
            expired=True,
        )
        start_group = TaskGroup(date_str=first_task.get_date_key(),
                                tasks=[first_task])
        self.task_manager.task_groups = [start_group]
        self.task_manager.save_task_groups()
    
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
