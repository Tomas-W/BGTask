import os
import json
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp

from src.screens.home.home_screen import HomeScreen
from src.screens.new_task import NewTaskScreen

from src.settings import SCREEN


if platform != "android":
    Window.size = (412, 915)


class TaskApp(App):
    def build(self):
        self.title = "Task Manager"
        self.sm = ScreenManager(transition=SlideTransition())
        
        self.home_screen = HomeScreen(name=SCREEN.HOME)
        self.task_screen = NewTaskScreen(name=SCREEN.NEW_TASK)
        
        self.sm.add_widget(self.home_screen)
        self.sm.add_widget(self.task_screen)
        
        return self.sm
    
    def on_start(self):
        self.home_screen.load_tasks()


if __name__ == "__main__":
    TaskApp().run()
