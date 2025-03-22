from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.utils import platform

from src.screens.home.home_screen import HomeScreen
from src.screens.new_task.new_task import NewTaskScreen
from src.screens.select_date.select_date import SelectDate
from src.settings import SCREEN


if platform != "android":
    Window.size = (390, 790)
    Window.left = -450
    Window.top = 350


class TaskApp(App):
    def build(self):
        self.title = "Task Manager"
        self.sm = ScreenManager(transition=SlideTransition())
        
        self.home_screen = HomeScreen(name=SCREEN.HOME)
        self.task_screen = NewTaskScreen(name=SCREEN.NEW_TASK)
        self.select_date_screen = SelectDate(name=SCREEN.SELECT_DATE)

        self.sm.add_widget(self.home_screen)
        self.sm.add_widget(self.task_screen)
        self.sm.add_widget(self.select_date_screen)
        
        return self.sm
    
    def on_start(self):
        self.home_screen.load_tasks()


if __name__ == "__main__":
    TaskApp().run()
