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
        global start_time
        self.start_time = start_time
        
        # Only create what's needed for the start screen
        from kivy.uix.screenmanager import ScreenManager, SlideTransition
        self.screen_manager = ScreenManager(transition=SlideTransition())
        
        # StartScreen
        start_time = time.time()
        from src.screens.start.start_screen import StartScreen
        self.screens = {
            SCREEN.START: StartScreen(name=SCREEN.START)
        }
        self.screen_manager.add_widget(self.screens[SCREEN.START])
        end_time = time.time()
        self.start_screen_time = end_time - start_time
        
        return self.screen_manager
    
    def get_screen(self, screen_name):
        return self.screens.get(screen_name)
    
    def _load_app_components(self):
        self._init_logger()
        self.logger.error(f"StartScreen time: {self.start_screen_time}")
        self._init_managers()
        self._init_screens()
    
    def _init_managers(self):
        start_time = time.time()
        from src.managers.navigation_manager import NavigationManager
        self.navigation_manager = NavigationManager(
            screen_manager=self.screen_manager,
            start_screen=SCREEN.HOME
        )
        end_time = time.time()
        self.logger.error(f"Init NavigationManager time: {end_time - start_time}")

        start_time = time.time()
        from src.managers.tasks.task_manager import TaskManager
        self.task_manager = TaskManager() 
        end_time = time.time()
        self.logger.error(f"Init TaskManager time: {end_time - start_time}")

        def init_audio_manager(dt):
            start_time = time.time()
            self.logger.warning(f"Init AudioManager STARTING AT {start_time}")
            from src.managers.audio.audio_manager import AudioManager
            self.audio_manager = AudioManager()
            end_time = time.time()
            self.logger.warning(f"Init AudioManager time: {end_time - start_time}")

        def connect_audio_screens(dt):
            self.screens[SCREEN.SELECT_ALARM].audio_manager = self.audio_manager
            self.screens[SCREEN.SAVED_ALARMS].audio_manager = self.audio_manager
            self.screens[SCREEN.NEW_TASK].audio_manager = self.audio_manager

        
        from kivy.clock import Clock
        # Timings are 'linked'
        Clock.schedule_once(init_audio_manager, 0)
        Clock.schedule_once(connect_audio_screens, 0.3)
    
    def _init_screens(self):
    # HomeScreen
        start_time = time.time()
        from src.screens.home.home_screen import HomeScreen
        self.screens[SCREEN.HOME] = HomeScreen(name=SCREEN.HOME,
                                               navigation_manager=self.navigation_manager,
                                               task_manager=self.task_manager)
        end_time = time.time()
        self.logger.error(f"Init HomeScreen time: {end_time - start_time}")

    # NewTaskScreen
        start_time = time.time()
        from src.screens.new_task.new_task_screen import NewTaskScreen
        self.screens[SCREEN.NEW_TASK] = NewTaskScreen(name=SCREEN.NEW_TASK,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager,
                                                    audio_manager=None)
        end_time = time.time()
        self.logger.error(f"Init NewTaskScreen time: {end_time - start_time}")

    # SelectDateScreen
        start_time = time.time()
        from src.screens.select_date.select_date_screen import SelectDateScreen
        self.screens[SCREEN.SELECT_DATE] = SelectDateScreen(name=SCREEN.SELECT_DATE,
                                                             navigation_manager=self.navigation_manager,
                                                             task_manager=self.task_manager)
        end_time = time.time()
        self.logger.error(f"Init SelectDateScreen time: {end_time - start_time}")

    # SelectAlarmScreen
        start_time = time.time()
        from src.screens.select_alarm.select_alarm_screen import SelectAlarmScreen
        self.screens[SCREEN.SELECT_ALARM] = SelectAlarmScreen(name=SCREEN.SELECT_ALARM,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=None)
        end_time = time.time()
        self.logger.error(f"Init SelectAlarmScreen time: {end_time - start_time}")

    # SavedAlarmScreen
        start_time = time.time()
        from src.screens.saved_alarm.saved_alarm_screen import SavedAlarmScreen
        self.screens[SCREEN.SAVED_ALARMS] = SavedAlarmScreen(name=SCREEN.SAVED_ALARMS,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=None)
        end_time = time.time()
        self.logger.error(f"Init SavedAlarmScreen time: {end_time - start_time}")

    # SettingsScreen
        start_time = time.time()
        from src.screens.settings.settings_screen import SettingsScreen
        self.screens[SCREEN.SETTINGS] = SettingsScreen(name=SCREEN.SETTINGS,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager)
        end_time = time.time()
        self.logger.error(f"Init SettingsScreen time: {end_time - start_time}")

    # Add screens to screen manager
        for screen_name, screen in self.screens.items():
            if screen_name != SCREEN.START:
                self.screen_manager.add_widget(screen)
        
    # Set Screen attributes
        from kivy.clock import Clock
        start_screen = self.get_screen(SCREEN.START)
        Clock.schedule_once(lambda *args: setattr(start_screen, "home_screen_ready", True), 0)
        home_screen = self.get_screen(SCREEN.HOME)
        Clock.schedule_once(lambda *args: setattr(home_screen, "new_task_screen_ready", True), 0.3)

        finish_time = time.time()
        self.logger.warning(f"TOTAL TIME TO LOAD APP MINUS AUDIO MANAGER: {finish_time - self.start_time}")
        self.logger.warning(f"FINISHED INITIALIZING APP AT {finish_time}")
    
    def _init_logger(self):
        from src.utils.logger import logger
        self.logger = logger


if __name__ == "__main__":
    TaskApp().run()
