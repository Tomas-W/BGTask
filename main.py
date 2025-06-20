from src.utils.timer import TIMER
TIMER.start("start")

from src.utils.logger import logger
logger.timing(f"Starting main.py")

TIMER.start("start_kivy")
from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.core.window import Window
from kivy.utils import platform

TIMER.stop("start_kivy")
logger.timing(f"Loading Kivy took: {TIMER.get_time('start_kivy')}")

from managers.device.device_manager import DM
from src.utils.wrappers import log_time


from src.settings import SCREEN

if platform != "android":
    Window.size = (360, 736)
    Window.dpi = 100
    Window.left = -386
    Window.top = 316


# TODO: Trigger laarm dont change nbutton states
# TODO: Save user background and add retore option


# Widgets
# TODO: Base widgets and custom - with extra options like borders / radius / etc


# TaskManager


# ExpiryManager
# TODO: Trigger vibrate when App in foreground?


# BaseScreen


# HomeScreen
# TODO: Smart rendering widgets
# TODO: Create generic popup for errors


# NewTaskScreen
# TODO: Autofocus on input field when field error


# SelectDateScreen
# TODO: Optimize layout / widgets
# TODO: Wider input field for better selecting
# TODO: Block dates in past

# SelectAlarmScreen
# TODO: Repeat alarm
# TODO: Clean user input (maybe a popup level?)


# SavedAlarmScreen


# General
# TODO: Non confim buttons must be custom buttons, regular color is active, active color is custom confirm active
# TODO: When AudioManager is initialized without audio player, prevent audio functionality
# TODO: Button feedback
# TODO: Look at caching

# Service


TIMER.start("start_app")

class TaskApp(App, EventDispatcher):
    """
    TaskApp is the main class that is used to run the App.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)        
        self.active_popup = None

    def build(self):
        """
        Builds the App.
        """
        self.title = "Task Manager"
        
        self._init_screen_manager()
        self._init_navigation_manager()
        
        self._init_expiry_manager()
        self._init_task_manager()
        self.expiry_manager._connect_task_manager(self.task_manager)
        
        self._init_home_screen()
        
        return self.screen_manager
    
    def get_screen(self, screen_name):
        return self.screens.get(screen_name)

    def load_app(self, *args):
        """
        Loads rest of the App.
        """
        Clock.schedule_once(self._load_app, 0.1)
    
    def _load_app(self, *args):
        """
        Called when HomeScreen is finished loading.
        """
        self._init_audio_manager()

        self._init_communication_manager()
        self.expiry_manager._connect_communication_manager(self.communication_manager)
        self.task_manager._connect_communication_manager(self.communication_manager)

        self._init_popup_manager()

        self._init_new_task_screen()
        self._init_settings_screen()

        self._init_select_date_screen()
        self._init_select_alarm_screen()
        self._init_saved_alarm_screen()

        self._init_service_permissions()

        self._log_loading_times()
    
    ###############################################
    ################### EVENTS ####################
    def on_stop(self):
        super().on_stop()
        logger.debug("App is stopping")
        # from profiler.profiler import profiler
        # profiler.stop()
    
    def on_pause(self):
        super().on_pause()
        logger.debug("App is pausing")
        return True
    
    def on_start(self):
        """
        Called after HomeScreen's pre_enter.
        """
        super().on_start()
        print("ON START ON START ON START ON START ON START ON START")

    def on_resume(self):
        """
        App is resumed from a paused state.
        """
        super().on_resume()
        logger.debug("App is resuming")

        self.audio_manager.stop_alarm()
        self.communication_manager.send_action(DM.ACTION.STOP_ALARM)
    
    ###############################################
    ################### MISC ######################
    @log_time("ServicePermissions")
    def _init_service_permissions(self):
        from src.managers.permission_manager import PM
        PM.validate_permission(PM.POST_NOTIFICATIONS)
        PM.validate_permission(PM.REQUEST_SCHEDULE_EXACT_ALARM)
        PM.validate_permission(PM.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
    
    def _log_loading_times(self, *args) -> None:
        """Logs all loading times from the TIMER."""
        from src.utils.timer import TIMER
        TIMER.stop("start_app")
        TIMER.stop("start")
        all_logs = TIMER.get_all_logs()
        for log in all_logs:
            logger.timing(log)
    
    ###############################################
    ################### MANAGERS ##################
    @log_time("ScreenManager")
    def _init_screen_manager(self):
        from kivy.uix.screenmanager import ScreenManager, SlideTransition
        self.screen_manager = ScreenManager(transition=SlideTransition())
        DM.LOADED.SCREEN_MANAGER = True
    
    @log_time("NavigationManager")
    def _init_navigation_manager(self):
        from src.managers.navigation_manager import NavigationManager
        self.navigation_manager = NavigationManager(
            app=self,
            start_screen=DM.SCREEN.HOME
        )
        DM.LOADED.NAVIGATION_MANAGER = True
    
    @log_time("ExpiryManager")
    def _init_expiry_manager(self):
        from src.managers.app_expiry_manager import AppExpiryManager
        self.expiry_manager = AppExpiryManager(app=self)
        DM.LOADED.EXPIRY_MANAGER = True
    
    @log_time("TaskManager")
    def _init_task_manager(self):
        from src.managers.app_task_manager import TaskManager
        self.task_manager = TaskManager(app=self)
        DM.LOADED.TASK_MANAGER = True
    
    @log_time("CommunicationManager")
    def _init_communication_manager(self):
        from src.managers.app_communication_manager import AppCommunicationManager
        self.communication_manager = AppCommunicationManager(app=self)
        DM.LOADED.COMMUNICATION_MANAGER = True
    
    @log_time("PopupManager")
    def _init_popup_manager(self):
        from managers.popups.popup_manager import _init_popup_manager
        _init_popup_manager(app=self)
        DM.LOADED.POPUP_MANAGER = True
    
    @log_time("AudioManager")
    def _init_audio_manager(self):
        from src.managers.app_audio_manager import AppAudioManager
        self.audio_manager = AppAudioManager(app=self)
        DM.LOADED.AUDIO_MANAGER = True
    
    ###############################################
    ################### SCREENS ###################
    @log_time("HomeScreen")
    def _init_home_screen(self):
        from src.screens.home.home_screen import HomeScreen
        self.screens = {
            SCREEN.HOME: HomeScreen(name=SCREEN.HOME,
                                    app=self)
            }
        self.screen_manager.add_widget(self.screens[SCREEN.HOME])
        DM.LOADED.HOME_SCREEN = True

    @log_time("NewTaskScreen")
    def _init_new_task_screen(self):
        from src.screens.new_task.new_task_screen import NewTaskScreen
        self.screens[SCREEN.NEW_TASK] = NewTaskScreen(name=SCREEN.NEW_TASK,
                                                      app=self)
        self.screen_manager.add_widget(self.screens[SCREEN.NEW_TASK])
        DM.LOADED.NEW_TASK_SCREEN = True
    
    @log_time("SettingsScreen")
    def _init_settings_screen(self):
        from src.screens.settings.settings_screen import SettingsScreen
        self.screens[SCREEN.SETTINGS] = SettingsScreen(name=SCREEN.SETTINGS,
                                                      app=self)
        self.screen_manager.add_widget(self.screens[SCREEN.SETTINGS])
        DM.LOADED.SETTINGS_SCREEN = True

    @log_time("SelectDateScreen")
    def _init_select_date_screen(self):
        from src.screens.select_date.select_date_screen import SelectDateScreen
        self.screens[SCREEN.SELECT_DATE] = SelectDateScreen(name=SCREEN.SELECT_DATE,
                                                            app=self)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_DATE])
        DM.LOADED.SELECT_DATE_SCREEN = True
    
    @log_time("SelectAlarmScreen")
    def _init_select_alarm_screen(self):
        from src.screens.select_alarm.select_alarm_screen import SelectAlarmScreen
        self.screens[SCREEN.SELECT_ALARM] = SelectAlarmScreen(name=SCREEN.SELECT_ALARM,
                                                            app=self)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_ALARM])
        DM.LOADED.SELECT_ALARM_SCREEN = True
    
    @log_time("SavedAlarmScreen")
    def _init_saved_alarm_screen(self):
        from src.screens.saved_alarm.saved_alarm_screen import SavedAlarmScreen
        self.screens[SCREEN.SAVED_ALARMS] = SavedAlarmScreen(name=SCREEN.SAVED_ALARMS,
                                                            app=self)
        self.screen_manager.add_widget(self.screens[SCREEN.SAVED_ALARMS])
        DM.LOADED.SAVED_ALARMS_SCREEN = True


if __name__ == "__main__":
    TaskApp().run()
