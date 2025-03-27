from kivy.app import App
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from src.managers.audio_manager import AudioManager
from src.managers.navigation_manager import NavigationManager
from src.managers.task_manager import TaskManager


from src.screens.home.home_screen import HomeScreen
from src.screens.new_task.new_task_screen import NewTaskScreen
from src.screens.select_date.select_date_screen import SelectDateScreen
from src.screens.select_alarm.select_alarm_screen import SelectAlarmScreen
from src.screens.saved_alarm.saved_alarm_screen import SavedAlarmScreen
from src.screens.settings.settings_screen import SettingsScreen

from src.settings import SCREEN, PLATFORM


# TODO: Add alarm path to task
# TODO: Add vibrtating to task
# TODO: Add alarm check to task

# TODO: Editing last task adds new default message
# TODO: Save scroll value when going to new task screen
# TODO: Look at caching
# TODO: Seperate logic in build method in main.py
# TODO: Add on_pause saving data
# TODO: Add on_resume loading data
# TODO: Add on_stop saving data
# TODO: Fix alarm name taken filename


if platform != PLATFORM.ANDROID:
    Window.size = (390, 790)
    Window.left = -450
    Window.top = 350


class TaskApp(App):
    def build(self):
        self.title = "Task Manager"
        # Managers [order is important]
        self.screen_manager = ScreenManager(transition=SlideTransition())
        self.navigation_manager = NavigationManager(
            screen_manager=self.screen_manager,
            start_screen=SCREEN.HOME
        )
        self.task_manager = TaskManager()
        self.audio_manager = AudioManager()

        # Screens
        self.screens = {
            SCREEN.HOME: HomeScreen(name=SCREEN.HOME,
                                    navigation_manager=self.navigation_manager,
                                    task_manager=self.task_manager),
            SCREEN.NEW_TASK: NewTaskScreen(name=SCREEN.NEW_TASK,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager,
                                           audio_manager=self.audio_manager),
            SCREEN.SELECT_DATE: SelectDateScreen(name=SCREEN.SELECT_DATE,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager),
            SCREEN.SELECT_ALARM: SelectAlarmScreen(name=SCREEN.SELECT_ALARM,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager,
                                           audio_manager=self.audio_manager),
            SCREEN.SAVED_ALARMS: SavedAlarmScreen(name=SCREEN.SAVED_ALARMS,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager,
                                           audio_manager=self.audio_manager),
            SCREEN.SETTINGS: SettingsScreen(name=SCREEN.SETTINGS,
                                           navigation_manager=self.navigation_manager,
                                           task_manager=self.task_manager),
        }
        for screen_name, screen in self.screens.items():
            self.screen_manager.add_widget(screen)

        return self.screen_manager
    
    def get_screen(self, screen_name):
        return self.screens.get(screen_name)

    def on_start(self):
        self.screens[SCREEN.HOME].load_tasks()


if __name__ == "__main__":
    TaskApp().run()
