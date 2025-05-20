import time

starting_time = time.time()

start_kivy_time = time.time()
from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher

from kivy.core.window import Window
from kivy.utils import platform

from src.settings import SCREEN, PLATFORM, LOADED
kivy_time = time.time() - start_kivy_time
print(f"FINISHED KIVY TIME: {kivy_time:.4f}")

if platform != PLATFORM.ANDROID:
    Window.size = (360, 736)
    Window.dpi = 100
    Window.left = -386
    Window.top = 316


# TODO: Trigger laarm dont change nbutton states


# Widgets
# TODO: Base widgets and custom - with extra options like borders / radius / etc


# Popups
# TODO: Load popups background & connect later


# TaskManager


# StartScreen
# TODO: Refactor StartScreen / Layout / Widgets
# TODO: Smart loading widgets


# BaseScreen
# TODO: Fix synchronized_animate SIZE.BOTTOM_BAR_HEIGHT*1.05


# HomeScreen
# TODO: Smart rendering widgets
# TODO: Create generic popup for errors
# TODO: Floating Day label if many/long tasks
# TODO: Add year to Tasks header when in next year


# NewTaskScreen
# TODO: Autofocus on input field when field error


# SelectDateScreen
# TODO: Optimize layout / widgets
# TODO: Wider input field for better selecting
# TODO: Block dates in past

# SelectAlarmScreen
# TODO: Rename o existing name -> error popup
# TODO: Cache alarm buttons
# TODO: Limit alarm name length
# TODO: Repeat alarm


# SavedAlarmScreen



# General
# TODO: Non confim buttons must be custom buttons, regular color is active, active color is custom confirm active
# TODO: Rework is_android
# TODO: When AudioManager is initialized without audio player, prevent audio functionality
# TODO: Button feedback
# TODO: Look at caching
# TODO: Fix black alarm/vibrate icons for Tasks [TRYING]
# TODO: Slow L&R swiping for screens

# Service


start_app_time = time.time()

class TaskApp(App, EventDispatcher):
    """
    TaskApp is the main class that is used to run the app.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_start_screen_finished_load_app")
        
        self.active_popup = None
        
        self.starting_time = starting_time
        self.kivy_time = kivy_time
        self.start_app_time = start_app_time
    
    def build(self):
        """
        Builds the app.
        Only creates what's needed for the start screen to be shown.
        As soon as the start screen is shown, the rest of the app is loaded in the background.
        """
        self.title = "Task Manager"

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
    
    def on_start_screen_finished_load_app(self, *args):
        """
        Handler for start_screen_finished_load_app event
        Loads app components in priority order with schedule events.
        - Finish setting up StartScreen
        - Load HomeScreen
        - Load secondary Managers and Screens
        """
        Clock.schedule_once(self._load_start_components, 0.1)
    
    def _load_start_components(self, dt):
        self._init_logger()
        self.logger.critical(f"Loading StartScreen time: {self.start_screen_time:.4f}")

        self._init_navigation_manager()
        self._init_task_manager()
        self._connect_managers_to_start_screen(
            navigation_manager=self.navigation_manager,
            task_manager=self.task_manager
        )
        Clock.schedule_once(self._load_home_components, 0.05)
    
    def _load_home_components(self, dt):
        self._init_home_screen()
        self._build_home_screen()
        Clock.schedule_once(self._load_secondary_components, 0.05)

    def _load_secondary_components(self, dt):
        self._init_audio_manager()
        self._init_main_screens()
        self._init_secondary_screens()
        self._init_permissions()
    
    def _build_home_screen(self):
        self.get_screen(SCREEN.HOME)._full_rebuild_task_display()
    
    def _connect_managers_to_start_screen(self, navigation_manager, task_manager):
        self.get_screen(SCREEN.START).navigation_manager = navigation_manager
        self.get_screen(SCREEN.START).task_manager = task_manager
    
    def _init_navigation_manager(self):
        # NavigationManager
        start_time = time.time()
        from src.managers.navigation_manager import NavigationManager
        self.navigation_manager = NavigationManager(
            screen_manager=self.screen_manager,
            start_screen=SCREEN.HOME
        )
    
    def _init_task_manager(self):
        # TaskManager
        start_time = time.time()
        from src.managers.tasks.task_manager import TaskManager
        self.task_manager = TaskManager()
        LOADED.TASK_MANAGER = True
        self.logger.critical(f"Loading TaskManager time: {time.time() - start_time:.4f}")
    
    def _init_audio_manager(self):
        # AudioManager
        start_time = time.time()
        from src.managers.audio.audio_manager import AudioManager
        self.audio_manager = AudioManager()
        LOADED.AUDIO_MANAGER = True
        self.logger.critical(f"Loading AudioManager time: {time.time() - start_time:.4f}")
    
    def _init_home_screen(self):
        # HomeScreen
        start_time = time.time()
        from src.screens.home.home_screen import HomeScreen
        self.screens[SCREEN.HOME] = HomeScreen(name=SCREEN.HOME,
                                               navigation_manager=self.navigation_manager,
                                               task_manager=self.task_manager)
        LOADED.HOME = True
        self.logger.critical(f"Loading HomeScreen time: {time.time() - start_time:.4f}")

    def _init_main_screens(self):
        # NewTaskScreen
        start_time = time.time()
        from src.screens.new_task.new_task_screen import NewTaskScreen
        self.screens[SCREEN.NEW_TASK] = NewTaskScreen(name=SCREEN.NEW_TASK,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager,
                                                    audio_manager=self.audio_manager)
        self.logger.critical(f"Loading NewTaskScreen time: {time.time() - start_time:.4f}")

        # SettingsScreen
        start_time = time.time()
        from src.screens.settings.settings_screen import SettingsScreen
        self.screens[SCREEN.SETTINGS] = SettingsScreen(name=SCREEN.SETTINGS,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager)
        self.logger.critical(f"Loading SettingsScreen time: {time.time() - start_time:.4f}")

        # Add screens to screen manager
        for screen_name, screen in self.screens.items():
            if screen_name != SCREEN.START:
                self.screen_manager.add_widget(screen)
        
        LOADED.NEW_TASK = True
        LOADED.SETTINGS = True
    
    def _init_secondary_screens(self):
        # SelectDateScreen
        start_time = time.time()
        from src.screens.select_date.select_date_screen import SelectDateScreen
        self.screens[SCREEN.SELECT_DATE] = SelectDateScreen(name=SCREEN.SELECT_DATE,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_DATE])
        self.logger.critical(f"Loading SelectDateScreen time: {time.time() - start_time:.4f}")

        # SelectAlarmScreen
        start_time = time.time()
        from src.screens.select_alarm.select_alarm_screen import SelectAlarmScreen
        self.screens[SCREEN.SELECT_ALARM] = SelectAlarmScreen(name=SCREEN.SELECT_ALARM,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=self.audio_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_ALARM])
        self.logger.critical(f"Loading SelectAlarmScreen time: {time.time() - start_time:.4f}")

        # SavedAlarmScreen
        start_time = time.time()
        from src.screens.saved_alarm.saved_alarm_screen import SavedAlarmScreen
        self.screens[SCREEN.SAVED_ALARMS] = SavedAlarmScreen(name=SCREEN.SAVED_ALARMS,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=self.audio_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SAVED_ALARMS])
        self.logger.critical(f"Loading SavedAlarmScreen time: {time.time() - start_time:.4f}")

        LOADED.SELECT_DATE = True
        LOADED.SELECT_ALARM = True
    
    def _init_permissions(self):
        # Request runtime permissions for Android
        if platform == "android":
            from android.permissions import request_permissions, Permission  # type: ignore
            permissions = [
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.RECORD_AUDIO,
                Permission.POST_NOTIFICATIONS
            ]
            request_permissions(permissions)


    def _init_logger(self):
        from src.utils.logger import logger
        self.logger = logger
    
    def on_pause(self):
        """
        App is paused by the OS (e.g., user switches to another app).
        Creates a flag file to indicate Tasks need updating in the service.
        """
        self.logger.debug("App is pausing")
        self.task_manager._checked_background_cancelled_tasks = False
        return True
    
    def on_stop(self):
        """
        App is being stopped.
        Save last open time and ensure the background service is running.
        """
        self.logger.debug("App is stopping - saving last open for background service")
        
    def on_resume(self):
        """
        App is resumed from a paused state.
        Check for any expired tasks that might have occurred while paused.
        """
        self.logger.debug("App is resuming - checking for expired tasks")

        if hasattr(self, "task_manager"):
            # Reload tasks
            start_time = time.time()
            # First reload tasks from file to ensure we have latest data
            self.task_manager.tasks_by_date = self.task_manager._load_tasks_by_date()
            # Then update expired tasks
            self.task_manager.set_expired_tasksbydate()
            # Finally rebuild the display with updated data
            self.get_screen(SCREEN.HOME)._full_rebuild_task_display()
            self.logger.critical(f"Reloading Tasks on_resume took: {time.time() - start_time:.4f}")
    
    def on_start(self):
        """
        App is being started.
        """
        print("on_start")

    def _check_background_cancelled_tasks(self, dt):
        """
        Check for any cancelled tasks that might have occurred while paused.
        """
        if not self.task_manager:
            return
        
        self.task_manager.check_background_cancelled_tasks()
        Clock.unschedule(self._check_background_cancelled_tasks)


if __name__ == "__main__":
    TaskApp().run()
