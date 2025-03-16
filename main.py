import os
import json
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp

from src.screens.home import HomeScreen
from src.screens.new_task import TaskScreen
import src.settings as settings

# Set window size for desktop testing
if platform != "android":
    Window.size = (412, 915)  # This is specific to desktop testing, we'll leave it as hardcoded

class TaskApp(App):
    def build(self):
        # Create and return the screen manager
        self.title = "Task Manager"
        self.sm = ScreenManager(transition=SlideTransition())
        
        # Add screens
        self.home_screen = HomeScreen(name="home")
        self.task_screen = TaskScreen(name="task")
        
        self.sm.add_widget(self.home_screen)
        self.sm.add_widget(self.task_screen)
        
        return self.sm
    
    def on_start(self):
        # Load tasks from storage if available
        self.home_screen.load_tasks()

if __name__ == "__main__":
    TaskApp().run() 