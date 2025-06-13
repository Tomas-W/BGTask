from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.animation import Animation

from src.screens.base.base_screen import BaseScreen
from managers.device.device_manager import DM
from .home_screen_utils import HomeScreenUtils
from src.screens.home.home_widgets import TaskGroupHeader

from src.utils.logger import logger
from src.settings import SCREEN, COL, SIZE, SPACE, FONT

if TYPE_CHECKING:
    from main import TaskApp
    from src.managers.navigation_manager import NavigationManager
    from src.managers.app_task_manager import TaskManager
    from managers.tasks.task import Task
    from src.screens.home.home_widgets import TaskLabel, TimeLabel


class HomeScreen(BaseScreen, HomeScreenUtils):
    """
    HomeScreen is the main screen for the app that:
    - Has a TopBar with options
    - Displays a list of Tasks grouped by date
    - Has a BottomBar with a scroll to top button
    """
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager

        self._home_screen_finished: bool = False
        # Scroll to Task
        self.task_header_widget: TaskGroupHeader | None = None
        self.time_label_widget: TimeLabel | None = None
        self.task_message_widget: TaskLabel | None = None
        # Task selection
        self.selected_task: Task | None = None
        self.selected_label: TaskLabel | None = None

        # TopBar
        top_bar_callback = self.navigate_to_new_task_screen
        top_left_callback = lambda instance: self.navigation_manager.navigate_to(SCREEN.START)
        self.top_bar.make_home_bar(top_left_callback=top_left_callback, top_bar_callback=top_bar_callback)
        # TopBarExpanded
        self.top_bar_expanded.make_home_bar(top_left_callback=top_left_callback)
        # Edit and delete buttons
        self.create_floating_action_buttons()
        # BottomBar
        self.add_bottom_bar()

        # Build Screen
        self._refresh_home_screen()
    
    def create_floating_action_buttons(self):
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
    
    def select_task(self, task, label=None):
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
    
    def show_floating_buttons(self):
        """Shows the floating action buttons with animation."""
        self.floating_button_container.opacity = 0
        self.floating_button_container.pos_hint = {"center_x": 0.5, "y": 0.05}
        animation = Animation(opacity=1, pos_hint={"center_x": 0.5, "y": 0.1}, duration=0.3)
        animation.start(self.floating_button_container)
    
    def hide_floating_buttons(self):
        """Hides the floating action buttons with animation."""
        animation = Animation(opacity=0, pos_hint={"center_x": 0.5, "y": 0.05}, duration=0.3)
        animation.start(self.floating_button_container)
    
    def edit_selected_task(self, instance):
        """Edits the currently selected Task."""
        if self.selected_task:
            task_id = str(self.selected_task.task_id)
            task_to_edit = self.task_manager.get_task_by_id_(task_id)
            if task_to_edit:
                self.app.get_screen(SCREEN.NEW_TASK).load_task_data(task=task_to_edit)
                Clock.schedule_once(lambda dt: self.navigation_manager.navigate_to(SCREEN.NEW_TASK), 0.1)
            else:
                logger.error(f"Error editing Task: {DM.get_task_id_log(task_id)} not found")
                self.refresh_home_screen()
                
            # Clean up selection state
            if self.selected_label:
                self.selected_label.set_selected(False)
            
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
    
    def delete_selected_task(self, instance):
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
    
    def navigate_to_new_task_screen(self, *args) -> None:
        """
        Navigates to the NewTaskScreen.
        If the edit/delete icons are visible, toggle them off first.
        Deselects any selected Task.
        """
        if not DM.LOADED.NEW_TASK_SCREEN:
            logger.error("NewTaskScreen not ready - cannot navigate to it")
            return
        
        # Deselect Task
        if self.selected_task:
            if self.selected_label:
                self.selected_label.set_selected(False)
            
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
        
        self.navigation_manager.navigate_to(DM.SCREEN.NEW_TASK)

    def find_task(self, instance, task) -> bool:
        """
        Searches for a Task's widgets and tries to save them.
        Returns True if all were found, False otherwise.
        """
        selected_task_group = self.get_task_group(task)
        if not selected_task_group:
            logger.error(f"Error finding task: {DM.get_task_id_log(task.task_id)} not found")
            return False
        
        # Save TaskHeader
        for child in selected_task_group.children:
            if isinstance(child, TaskGroupHeader):
                self.task_header_widget = child
                break
        
        # Find TaskContainer
        task_container = self.get_task_container(selected_task_group, task)
        if not task_container or not self.task_header_widget:
            return False
        
        # Save TaskLabel
        self.task_message_widget = self.get_task_message_widget(task_container)
        if not self.task_message_widget:
            return False
        
        return True

    def scroll_to_task(self, task):
        """Schedules to scroll to the Task."""
        Clock.schedule_once(lambda dt: self._scroll_to_task(instance=None, task=task), 0.05)

    def _scroll_to_task(self, instance, task, *args, **kwargs):
        """Scrolls to the Task."""
        if not self.find_task(instance, task):
            logger.error(f"Error scrolling to task: {DM.get_task_id_log(task.task_id)} not found")
            return
        
        self.scroll_container.scroll_view.scroll_y = 1.0

        # Scroll up to Task header
        if self.task_header_widget is not None:
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(self.task_header_widget, animate=False), 0.2)

        # Scroll down to task message and handle highlighting
        if self.task_message_widget is not None:
            # Store reference to avoid it being None later
            task_widget = self.task_message_widget
            Clock.schedule_once(lambda dt: self.scroll_container.scroll_view.scroll_to(task_widget, animate=False), 0.25)
            Clock.schedule_once(lambda dt: task_widget.set_active(True) if task_widget else None, 0.3)
            Clock.schedule_once(lambda dt: task_widget.set_active(False) if task_widget else None, 4)
            Clock.schedule_once(lambda dt: self.clear_go_to_task_references(), 4.1)
        
    def refresh_home_screen(self, *args) -> None:
        """Schedules to refresh the HomeScreen."""
        Clock.schedule_once(lambda dt: self._refresh_home_screen(), 0.05)
    
    def _log_loading_times(self) -> None:
        """Logs all loading times from the TIMER."""
        from src.utils.timer import TIMER
        all_logs = TIMER.get_all_logs()
        for log in all_logs:
            logger.timing(log)
    
    def on_pre_enter(self) -> None:
        super().on_pre_enter()
    
    def on_enter(self) -> None:
        super().on_enter()
        # Connect initial_scroll flag to the scroll container
        self.scroll_container.initial_scroll = self.initial_scroll
        
        # First time enter
        if not self._home_screen_finished:
            self.scroll_container.scroll_view.scroll_y = 1.0
            self._log_loading_times()
            self._home_screen_finished = True
    
    def on_leave(self):
        super().on_leave()
        
        # Deselect Task
        if self.selected_task:
            if self.selected_label:
                self.selected_label.set_selected(False)
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
