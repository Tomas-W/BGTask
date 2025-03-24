from kivy.app import App
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from src.utils.navigation_manager import NavigationManager

from src.screens.home.home_screen import HomeScreen
from src.screens.new_task.new_task_screen import NewTaskScreen
from src.screens.select_date.select_date_screen import SelectDateScreen
from src.screens.settings.settings_screen import SettingsScreen

from src.utils.task_manager import TaskManager

from src.settings import SCREEN


if platform != "android":
    Window.size = (390, 790)
    Window.left = -450
    Window.top = 350


class TaskApp(App):
    def build(self):
        self.title = "Task Manager"
        self.sm = ScreenManager(transition=SlideTransition())
        self.navigation_manager = NavigationManager(
            screen_manager=self.sm,
            start_screen=SCREEN.HOME
        )
        self.task_manager = TaskManager()

        self.screens = {
            SCREEN.HOME: HomeScreen(name=SCREEN.HOME,
                                    navigation_manager=self.navigation_manager,
                                    task_manager=self.task_manager),
            SCREEN.NEW_TASK: NewTaskScreen(name=SCREEN.NEW_TASK,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager),
            SCREEN.SELECT_DATE: SelectDateScreen(name=SCREEN.SELECT_DATE,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager),
            SCREEN.SETTINGS: SettingsScreen(name=SCREEN.SETTINGS,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager),
        }

        for screen_name, screen in self.screens.items():
            self.sm.add_widget(screen)
        
        return self.sm
    
    def on_start(self):
        self.screens[SCREEN.HOME].load_tasks()


if __name__ == "__main__":
    TaskApp().run()
