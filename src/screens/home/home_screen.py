from datetime import datetime
import time
from kivy.uix.floatlayout import FloatLayout

from src.screens.base.base_screen import BaseScreen  # type: ignore
from .home_widgets import TaskGroup

from src.utils.bars import HomeBarClosed, HomeBarExpanded
from src.utils.buttons import BottomBar
from src.utils.containers import BaseLayout, ScrollContainer

from src.settings import TEXT, SCREEN


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

        self.show_hints = True
        self.edit_delete_visible = False
        self.edit_delete_buttons = []

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Basic TopBar
        self.top_bar = HomeBarClosed(
            edit_callback=self.toggle_edit_delete,
            new_task_callback=self.navigate_to_new_task,
            options_callback=lambda instance: self.switch_top_bar(),
        )
        # TopBar with expanded options
        self.top_bar_expanded = HomeBarExpanded(
            edit_callback=self.toggle_edit_delete,
            screenshot_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.START),
            options_callback=lambda instance: self.switch_top_bar(),
            settings_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.SETTINGS),
            exit_callback=self.navigation_manager.exit_app,
        )
        self.layout.add_widget(self.top_bar.top_bar_container)
        
        # Scrollable container for task groups
        self.scroll_container = ScrollContainer()

        # Bottom bar with ^ button
        self.bottom_bar = BottomBar(text="^")
        self.bottom_bar.bind(on_press=self.scroll_container.scroll_to_top)
        self.scroll_container.connect_bottom_bar(self.bottom_bar)
        
        # Apply layout
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.root_layout.add_widget(self.bottom_bar)
        self.add_widget(self.root_layout)
    
    def navigate_to_new_task(self, *args):
        """Navigate to the new task screen"""
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
    def check_for_edit_delete(self):
        """Check if there are any edit and delete buttons"""
        if self.edit_delete_visible:
            self.show_edit_delete()
        else:
            self.hide_edit_delete()
    
    def toggle_edit_delete(self, *args):
        """Toggle the edit and delete icons"""
        self.edit_delete_visible = not self.edit_delete_visible
        self.check_for_edit_delete()
    
    def show_edit_delete(self):
        """Show the edit and delete icons"""
        for button in self.edit_delete_buttons:
            button.set_opacity(1)
            button.set_disabled(False)
    
    def hide_edit_delete(self):
        """Hide the edit and delete icons"""
        for button in self.edit_delete_buttons:
            button.set_opacity(0)
            button.set_disabled(True)

    def load_tasks(self):
        """Load tasks from the task manager"""
        self.task_manager.load_tasks()
        self.update_task_display()
    
    def update_task_display(self):
        """Update the task display"""
        self.scroll_container.clear_widgets()
        
        task_groups = self.task_manager.get_tasks_by_date()        
        # Add task groups to display
        self.task_groups = []
        for group in task_groups:
            task_group = TaskGroup(
                date_str=group["date"],
                tasks=group["tasks"],
                size_hint=(1, None)
            )
            self.scroll_container.add_widget_to_container(task_group)
            self.task_groups.append(task_group)
        
        self.check_for_edit_delete()
    
    def on_pre_enter(self):
        """Called just before the screen is entered"""
        super().on_pre_enter()
        # Load tasks first
        self.task_manager.load_tasks()
        
        # Then check if we have any tasks
        if not self.task_manager.tasks and self.show_hints:
            self.task_manager.add_task(message=TEXT.NO_TASKS, timestamp=datetime.now())
            self.show_hints = False
        
        self.update_task_display()

    def on_enter(self):
        """Called when screen is entered"""
        on_enter_time = time.time()
        self.on_enter_time = on_enter_time