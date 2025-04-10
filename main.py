import time
start_kivy_time = time.time()

from kivy.app import App
from kivy.clock import Clock

from kivy.core.window import Window
from kivy.utils import platform

from src.settings import SCREEN, PLATFORM, LOADED

if platform != PLATFORM.ANDROID:
    Window.size = (360, 736)
    Window.dpi = 100
    Window.left = -386
    Window.top = 316

total_kivy_time = time.time() - start_kivy_time
print(f"LOADING KIVY TOOK: {total_kivy_time:.4f}")
print(f"LOADING KIVY TOOK: {total_kivy_time:.4f}")
print(f"LOADING KIVY TOOK: {total_kivy_time:.4f}")

# TaskManager
# TODO: Expired check only today
# TODO: Check every minute for expired tasks and update Task


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
# TODO: Cache alarm buttons


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
        self.start_kivy_time = start_kivy_time
        self.total_kivy_time = total_kivy_time

        from kivy.uix.screenmanager import ScreenManager, SlideTransition
        self.screen_manager = ScreenManager(transition=SlideTransition())
        
        # StartScreen
        create_start_screen_time = time.time()
        from src.screens.start.start_screen import StartScreen
        self.screens = {
            SCREEN.START: StartScreen(name=SCREEN.START)
        }
        self.screen_manager.add_widget(self.screens[SCREEN.START])
        self.start_screen_time = time.time() - create_start_screen_time
        
        return self.screen_manager
    
    def get_screen(self, screen_name):
        return self.screens.get(screen_name)
    
    def _load_app_components(self):
        self._init_logger()
        self.logger.error(f"Loading StartScreen time: {self.start_screen_time:.4f}")
        self._init_managers()
        self._init_screens()
    
    def _init_managers(self):
        # NavigationManager
        start_time = time.time()
        from src.managers.navigation_manager import NavigationManager
        self.navigation_manager = NavigationManager(
            screen_manager=self.screen_manager,
            start_screen=SCREEN.HOME
        )
        LOADED.NAVIGATION_MANAGER = True
        self.logger.error(f"Loading NavigationManager time: {time.time() - start_time:.4f}")

        # TaskManager
        start_time = time.time()
        from src.managers.tasks.task_manager import TaskManager
        self.task_manager = TaskManager() 
        LOADED.TASK_MANAGER = True
        self.logger.error(f"Loading TaskManager time: {time.time() - start_time:.4f}")

        # AudioManager
        start_time = time.time()
        from src.managers.audio.audio_manager import AudioManager
        self.audio_manager = AudioManager()
        LOADED.AUDIO_MANAGER = True
        self.logger.error(f"Loading AudioManager time: {time.time() - start_time:.4f}")

    def _init_screens(self):
        # HomeScreen
        start_time = time.time()
        from src.screens.home.home_screen import HomeScreen
        self.screens[SCREEN.HOME] = HomeScreen(name=SCREEN.HOME,
                                               navigation_manager=self.navigation_manager,
                                               task_manager=self.task_manager)
        LOADED.HOME = True
        self.logger.error(f"Loading HomeScreen time: {time.time() - start_time:.4f}")

        # NewTaskScreen
        start_time = time.time()
        from src.screens.new_task.new_task_screen import NewTaskScreen
        self.screens[SCREEN.NEW_TASK] = NewTaskScreen(name=SCREEN.NEW_TASK,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager,
                                                    audio_manager=None)
        LOADED.NEW_TASK = True
        self.logger.error(f"Loading NewTaskScreen time: {time.time() - start_time:.4f}")

        # SettingsScreen
        start_time = time.time()
        from src.screens.settings.settings_screen import SettingsScreen
        self.screens[SCREEN.SETTINGS] = SettingsScreen(name=SCREEN.SETTINGS,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager)
        LOADED.SETTINGS = True
        self.logger.error(f"Loading SettingsScreen time: {time.time() - start_time:.4f}")

        # Add screens to screen manager
        for screen_name, screen in self.screens.items():
            if screen_name != SCREEN.START:
                self.screen_manager.add_widget(screen)
        
        Clock.schedule_once(lambda dt: self.get_screen(SCREEN.HOME)._full_rebuild_task_display(), 0.1)
        self.logger.debug(f"CALLING INIT OTHER SCREENS")
        self._init_other_screens(dt=None)
    
    def _init_other_screens(self, dt):
        # SelectDateScreen
        start_time = time.time()
        from src.screens.select_date.select_date_screen import SelectDateScreen
        self.screens[SCREEN.SELECT_DATE] = SelectDateScreen(name=SCREEN.SELECT_DATE,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_DATE])
        LOADED.SELECT_DATE = True
        self.logger.error(f"Loading SelectDateScreen time: {time.time() - start_time:.4f}")

        # SelectAlarmScreen
        start_time = time.time()
        from src.screens.select_alarm.select_alarm_screen import SelectAlarmScreen
        self.screens[SCREEN.SELECT_ALARM] = SelectAlarmScreen(name=SCREEN.SELECT_ALARM,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=None)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_ALARM])
        LOADED.SELECT_ALARM = True
        self.logger.error(f"Loading SelectAlarmScreen time: {time.time() - start_time:.4f}")

        # SavedAlarmScreen
        start_time = time.time()
        from src.screens.saved_alarm.saved_alarm_screen import SavedAlarmScreen
        self.screens[SCREEN.SAVED_ALARMS] = SavedAlarmScreen(name=SCREEN.SAVED_ALARMS,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=None)
        self.screen_manager.add_widget(self.screens[SCREEN.SAVED_ALARMS])
        LOADED.SAVED_ALARMS = True
        self.logger.error(f"Loading SavedAlarmScreen time: {time.time() - start_time:.4f}")

        self.connect_audio_screens()
    
    def connect_audio_screens(self):
        self.screens[SCREEN.SELECT_ALARM].audio_manager = self.audio_manager
        self.screens[SCREEN.SAVED_ALARMS].audio_manager = self.audio_manager
        self.screens[SCREEN.NEW_TASK].audio_manager = self.audio_manager
    
    def _init_logger(self):
        from src.utils.logger import logger
        self.logger = logger
    
    def on_pause(self):
        """
        App is paused by the OS (e.g., user switches to another app).
        Backup the database to ensure data is persisted.
        """
        if hasattr(self, 'task_manager'):
            self.task_manager.save_tasks_to_json()
                
        return True
    
    def on_resume(self):
        """
        App is resumed from a paused state.
        Check for any expired tasks that might have occurred while paused.
        """
        if hasattr(self, 'task_manager'):
            self.task_manager.set_expired_tasks()


if __name__ == "__main__":
    TaskApp().run()
