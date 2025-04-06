import sys
import time
start_time = time.time()

from kivy.app import App
from src.settings import SCREEN, PLATFORM


from kivy.core.window import Window
from kivy.utils import platform

if platform != PLATFORM.ANDROID:
    Window.size = (360, 736)
    Window.dpi = 100
    Window.left = -386
    Window.top = 316


# TaskManager
# TODO: Expired check only today


# StartScreen
# TODO: Refactor StartScreen / Layout / Widgets
# TODO: When no tasks, edit message for screenshot
# TODO: Smart loading widgets


# BaseScreen
# TODO: Fix synchronized_animate SIZE.BOTTOM_BAR_HEIGHT*1.05


# HomeScreen
# TODO: Smart rendering widgets
# TODO: Hide edit/delete when not in edit mode in on_enter on HomeScreen
# TODO: Create generic popup for errors
# TODO: Only show tasks/edit/delete if visible
# TODO: Save scroll value when going to new task screen
# TODO: Floating Day label if many/long tasks


# NewTaskScreen
# TODO: 1 Task per timestamp
# TODO: Delete alarm button on NewTask screen
# TODO: After saving task, reset task details
# TODO: Remove selected_task_alarm after saving
# TODO: Prevent Tasks at same time


# SelectDateScreen


# SelectAlarmScreen
# TODO: Save - Alarm Name - Delete [with confirmation]
# TODO: PLay - Stop - Rename
# TODO: Rework audio preview
# TODO: Fix alarm name taken filename


# SavedAlarmScreen


# General
# TODO: When AudioManager is initialized without audio player, prevent audio functionality
# TODO: Button feedback
# TODO: Add alarm path to task
# TODO: Add vibrtating to task
# TODO: Look at caching
# TODO: Add on_pause saving data
# TODO: Add on_resume loading data
# TODO: Add on_stop saving data


class TaskApp(App):
    """
    TaskApp is the main class that is used to run the app.

    """
    def build(self):
        """
        Builds the app.
        Only creates what's needed for the start screen to be shown.
        As soon as the start screen is shown, the rest of the app is loaded in the background.
        """
        self.title = "Task Manager"
        self.start_time = start_time
        self.init_app_time = time.time()
        
        # Only create what's needed for the start screen
        from kivy.uix.screenmanager import ScreenManager, SlideTransition
        self.screen_manager = ScreenManager(transition=SlideTransition())
        
        from src.screens.start.start_screen import StartScreen
        self.screens = {
            SCREEN.START: StartScreen(name=SCREEN.START)
        }
        self.build_time = time.time()
        self.win_x, self.win_y = Window.size
        self.screen_manager.add_widget(self.screens[SCREEN.START])
        
        return self.screen_manager
    
    def get_screen(self, screen_name):
        return self.screens.get(screen_name)
    
    def _load_app_components(self):
        self._init_logger()
        self._init_managers()
        self._init_screens()
        self.finish_time = time.time()
        self._log_times()
    
    def _init_managers(self):
        from src.managers.audio.audio_manager import AudioManager
        from src.managers.navigation_manager import NavigationManager
        from src.managers.tasks.task_manager import TaskManager

        self.audio_manager = AudioManager()       
        self.navigation_manager = NavigationManager(
            screen_manager=self.screen_manager,
            start_screen=SCREEN.HOME
        )
        self.task_manager = TaskManager() 
    
    def _init_screens(self):
        from src.screens.home.home_screen import HomeScreen
        from src.screens.new_task.new_task_screen import NewTaskScreen
        from src.screens.select_date.select_date_screen import SelectDateScreen
        from src.screens.select_alarm.select_alarm_screen import SelectAlarmScreen
        from src.screens.saved_alarm.saved_alarm_screen import SavedAlarmScreen
        from src.screens.settings.settings_screen import SettingsScreen

        self.screens[SCREEN.HOME] = HomeScreen(name=SCREEN.HOME,
                                               navigation_manager=self.navigation_manager,
                                               task_manager=self.task_manager)

        self.screens[SCREEN.NEW_TASK] = NewTaskScreen(name=SCREEN.NEW_TASK,
                                                       navigation_manager=self.navigation_manager,
                                                       task_manager=self.task_manager,
                                                       audio_manager=self.audio_manager)
        self.screens[SCREEN.SELECT_DATE] = SelectDateScreen(name=SCREEN.SELECT_DATE,
                                                             navigation_manager=self.navigation_manager,
                                                             task_manager=self.task_manager)
        self.screens[SCREEN.SELECT_ALARM] = SelectAlarmScreen(name=SCREEN.SELECT_ALARM,
                                                               navigation_manager=self.navigation_manager,
                                                               task_manager=self.task_manager,
                                                               audio_manager=self.audio_manager)
        self.screens[SCREEN.SAVED_ALARMS] = SavedAlarmScreen(name=SCREEN.SAVED_ALARMS,
                                                               navigation_manager=self.navigation_manager,
                                                               task_manager=self.task_manager,
                                                               audio_manager=self.audio_manager)
        self.screens[SCREEN.SETTINGS] = SettingsScreen(name=SCREEN.SETTINGS,
                                                       navigation_manager=self.navigation_manager,
                                                       task_manager=self.task_manager)

        for screen_name, screen in self.screens.items():
            if screen_name != SCREEN.START:
                self.screen_manager.add_widget(screen)
    
    def _init_logger(self):
        from src.utils.logger import logger
        self.logger = logger
    
    def _log_times(self):
        self.on_enter_time = self.screens[SCREEN.START].on_enter_time
        self.logger.warning(f"Init app time: {self.init_app_time - self.start_time} seconds")
        self.logger.warning(f"On enter time: {self.on_enter_time - self.start_time} seconds")
        self.logger.warning(f"Build time: {self.build_time - self.start_time} seconds")
        self.logger.warning(f"Finished time: {self.finish_time - self.start_time} seconds")


if __name__ == "__main__":
    TaskApp().run()
