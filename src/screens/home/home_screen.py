from datetime import datetime
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from .home_utils import TaskGroup
from src.utils.buttons import TopBarButton, TopBar, BottomBar
from src.utils.containers import BaseLayout, ScrollContainer, TopBarContainer
from src.utils.taskmanager import TaskManager

from src.settings import SCREEN, TEXT, SPACE, PATH


class HomeScreen(Screen):
    """
    HomeScreen is the main screen for the app that:
    - Has a top bar with a settings button, new task button, and exit button
    - Displays a list of tasks grouped by date
    - Has a bottom bar with a scroll to top button
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_manager = TaskManager()

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar
        self.top_bar_container = TopBarContainer()
        # Settings button
        self.settings_button = TopBarButton(img_path=PATH.SETTINGS_IMG, side="left")
        self.top_bar_container.add_widget(self.settings_button)
        # New task button
        self.top_bar = TopBar(text="+")
        self.top_bar.bind(on_press=self.go_to_new_task_screen)
        self.top_bar_container.add_widget(self.top_bar)
        # Exit button
        self.exit_button = TopBarButton(img_path=PATH.EXIT_IMG, side="right")
        self.top_bar_container.add_widget(self.exit_button)

        self.layout.add_widget(self.top_bar_container)
        
        
        # Scrollable container for task groups
        self.scroll_container = ScrollContainer()
        self.scroll_container.container.spacing = SPACE.SPACE_MAX

        # Bottom bar with ^ button
        self.bottom_bar = BottomBar(text="^")
        self.bottom_bar.bind(on_press=self.scroll_container.scroll_to_top)
        self.scroll_container.connect_bottom_bar(self.bottom_bar)
        
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.root_layout.add_widget(self.bottom_bar)
        self.add_widget(self.root_layout)
            
    def go_to_new_task_screen(self, instance):
        self.manager.current = SCREEN.NEW_TASK
    
    def load_tasks(self):
        """Load tasks from the task manager"""
        self.task_manager.load_tasks()
        self.update_task_display()
    
    def update_task_display(self):
        """Update the task display"""
        self.scroll_container.clear_widgets()
        
        task_groups = self.task_manager.get_tasks_by_date()
        # Add no tasks message if no tasks
        if not task_groups:
            self.task_manager.add_task(message=TEXT.NO_TASKS, timestamp=datetime.now())
            return
        
        # Add task groups to display
        for group in task_groups:
            task_group = TaskGroup(
                date_str=group["date"],
                tasks=group["tasks"],
                size_hint=(1, None)
            )
            self.scroll_container.add_widget_to_container(task_group)
    
    def on_pre_enter(self):
        """Called just before the screen is entered"""
        if not self.task_manager.tasks:
            self.task_manager.add_task(message=TEXT.NO_TASKS, timestamp=datetime.now())
        
        self.update_task_display()

    def on_enter(self):
        """Called when screen is entered"""
        pass
    