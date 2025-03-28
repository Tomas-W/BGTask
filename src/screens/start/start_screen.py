import json
import sys
import time

from datetime import datetime
from pathlib import Path

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout

project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.append(project_root)

from src.utils.containers import BaseLayout
from src.settings import PATH


class StartScreen(Screen):
    """
    StartScreen is the first screen that is shown when the app is opened.
    It is a placeholder displaying the nearest expiring task while the app is loading.
    """
    def __init__(self, **kwargs):
        """
        Background is loaded and displayed.
        When the screen is shown, the page is built and the data is loaded in.
        """
        super().__init__(**kwargs)
        self.start_screen_loaded = False

        self.task_data = []
        self.task_date = ""

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()
        
        self.add_widget(self.root_layout)
    
    def _build_page(self):
        """
        Builds the page with the day header and the tasks container.
        """
        from src.utils.containers import ScrollContainer
        from src.screens.home.home_widgets import TaskHeader, TaskGroupContainer
        self.scroll_container = ScrollContainer()

        self.day_header = TaskHeader(text=self.task_date)
        self.scroll_container.container.add_widget(self.day_header)

        self.tasks_container = TaskGroupContainer()
        self.scroll_container.container.add_widget(self.tasks_container)

        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)

    def _load_current_tasks_widgets(self):
        """
        Loads the tasks widgets into the tasks container.
        These contain the next tasks that are expiring, grouped by date.
        """
        from src.screens.home.home_widgets import TaskContainer, TaskLabel, TimeLabel, TimeLabelContainer
        for task in self.task_data:
            task_container = TaskContainer()
            time_container = TimeLabelContainer()

            time = task["timestamp"].strftime("%H:%M")
            start_time_label = TimeLabel(text=time)
            start_time_label.size_hint_x = 0.3

            time_container.add_widget(start_time_label)
            task_container.add_widget(time_container)

            task_message = TaskLabel(text=task["message"])
            task_container.add_widget(task_message)

            self.tasks_container.add_widget(task_container)

    def _get_current_task_data(self):
        """
        Gets the current task data from the task file.
        It returns the first task that is expiring in the future.
        """
        try:
            with open(PATH.TASK_FILE, "r") as f:
                task_data = json.load(f)
            
            today = datetime.now().date()
            future_tasks = []
            for task in task_data:
                task_timestamp = datetime.fromisoformat(task["timestamp"])
                task_date = task_timestamp.date()
                
                if today <= task_date:
                    task["timestamp"] = task_timestamp
                    task["date"] = task_date
                    future_tasks.append(task)
            
            if not future_tasks:
                return []
            
            future_tasks.sort(key=lambda x: x["timestamp"])
            earliest_date = future_tasks[0]["date"]            
            return [task for task in future_tasks if task["date"] == earliest_date]
            
        except Exception as e:
            raise e
    
    def reset_start_screen(self, *args):
        """
        Reloads start screen data.
        """
        self.tasks_container.clear_widgets()
        self.task_data = self._get_current_task_data()
        self._load_current_tasks_widgets()

    @property
    def is_completed(self):
        return self.start_screen_loaded

    @is_completed.setter
    def is_completed(self, value):
        """
        Sets the start screen loaded to the value.
        Triggers loading the rest of the app in the background.
        """
        self.start_screen_loaded = value
        self.reset_start_screen()
        self.on_is_completed_change()

    def on_is_completed_change(self):
        """
        When the StartScreen is loaded, the rest of the app is loaded.
        """
        from kivy.clock import Clock
        Clock.schedule_once(self.background_load_app_components, 0.01)

    def background_load_app_components(self, dt):
        from kivy.app import App
        App.get_running_app()._load_app_components()

    def on_enter(self):
        """
        When the screen is shown, the page is built and the data is loaded in.
        """
        self.on_enter_time = time.time()        
        from kivy.clock import Clock
        Clock.schedule_once(self.load_data_background, 0.1)
        
    def load_data_background(self, dt):
        self._build_page()
        self.task_data = self._get_current_task_data()
        
        if self.task_data:
            task_date = self.task_data[0]["timestamp"].date()
            self.day_header.text = task_date.strftime("%A, %B %d, %Y")
            self._load_current_tasks_widgets()
        
        self.is_completed = True
