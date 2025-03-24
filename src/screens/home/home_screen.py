from datetime import datetime
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from .home_utils import TaskGroup, HomeBar, HomeBarExpanded
from src.utils.buttons import BottomBar
from src.utils.containers import BaseLayout, ScrollContainer

from src.settings import SCREEN, TEXT, SPACE


class HomeScreen(Screen):
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

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        self.top_bar_is_expanded = False
        # Basic TopBar
        self.top_bar = HomeBar(
            edit_callback=self.show_edit_icons,
            new_task_callback=self.navigation_manager.go_to_new_task_screen,
            options_callback=self.switch_top_bar,
        )
        # TopBar with expanded options
        self.top_bar_expanded = HomeBarExpanded(
            edit_callback=self.show_edit_icons,
            options_callback=self.switch_top_bar,
            settings_callback=self.navigation_manager.go_to_settings_screen,
            exit_callback=self.navigation_manager.exit_app,
        )
        self.layout.add_widget(self.top_bar.top_bar_container)
        
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
    
    def show_edit_icons(self, instance):
        pass
    
    def switch_top_bar(self, instance, on_enter=False):
        """Handle the clicked options"""
        if self.top_bar_is_expanded:
            self.layout.clear_widgets()
            self.layout.add_widget(self.top_bar_expanded.top_bar_container)
            self.layout.add_widget(self.scroll_container)
        else:
            self.layout.clear_widgets()
            self.layout.add_widget(self.top_bar.top_bar_container)
            self.layout.add_widget(self.scroll_container)
        if not on_enter:
            self.top_bar_is_expanded = not self.top_bar_is_expanded
    
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
        self.top_bar_is_expanded = False
        self.switch_top_bar(instance=None, on_enter=True)

        if not self.task_manager.tasks:
            self.task_manager.add_task(message=TEXT.NO_TASKS, timestamp=datetime.now())
        
        self.update_task_display()

    def on_enter(self):
        """Called when screen is entered"""
        pass
    
    def update_popup_background(self, dt):
        """Update the background rectangle position to match content"""
        # Find the content within the popup
        for child in self.options_popup.content.children:
            if isinstance(child, BoxLayout) and child.orientation == 'vertical':
                # Update rect position to match the content position
                self.rect.pos = child.pos
                self.rect.size = child.size
                break
            
    