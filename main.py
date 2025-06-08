import time

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
from src.utils.wrappers import log_time, android_only


from src.settings import SCREEN

if platform != "android":
    Window.size = (360, 736)
    Window.dpi = 100
    Window.left = -386
    Window.top = 316


# DeviceManager
# TODO: settings.LOADED to DM and include popup ect


# TODO: Trigger laarm dont change nbutton states


# Widgets
# TODO: Base widgets and custom - with extra options like borders / radius / etc


# Popups
# TODO: Load popups background & connect later


# TaskManager


# ExpiryManager
# TODO: Sync loop


# StartScreen
# TODO: Refactor StartScreen / Layout / Widgets
# TODO: Smart loading widgets
# TODO: Show snooze time
# TODO: Home and Start -> show cancelled future tasks muted colors

# BaseScreen
# TODO: Fix synchronized_animate SIZE.BOTTOM_BAR_HEIGHT*1.05


# HomeScreen
# TODO: Smart rendering widgets
# TODO: Create generic popup for errors
# TODO: Floating Day label if many/long tasks
# TODO: Add year to Tasks header when in next year
# TODO: Snooze/Cancel through notification -> update task display
# TODO: And immediate notification updates
# TODO: Show snooze time


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
# TODO: Clean user input (maybe a popup level?)


# SavedAlarmScreen



# General
# TODO: Non confim buttons must be custom buttons, regular color is active, active color is custom confirm active
# TODO: Rework is_android
# TODO: When AudioManager is initialized without audio player, prevent audio functionality
# TODO: Button feedback
# TODO: Look at caching
# TODO: Fix black alarm/vibrate icons for Tasks [TRYING]
# TODO: Slow L&R swiping for screens
# TODO: Task expired notification shows without snooze time
# TODO: Stop vibrate immediately
# TODO: Remove all App.get_running_app() and use dispatcher

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
        Only creates what's needed for the StartScreen to be shown.
        As soon as the StartScreen is shown, the rest of the App is loaded in the background.
        """
        self.title = "Task Manager"
        
        from kivy.uix.screenmanager import ScreenManager, SlideTransition
        self.screen_manager = ScreenManager(transition=SlideTransition())
        
        self._init_preference_manager()

        self._init_start_screen()
        
        return self.screen_manager
    
    def get_screen(self, screen_name):
        return self.screens.get(screen_name)
    
    def _load_app(self, *args):
        """
        Called when StartScreen is finished loading.
        Finishes loading StartScreen by adding NavigationManager and TaskManager.
        Then loads App components in priority order.
        """
        self._init_navigation_manager()
        self._init_task_manager()
        self._connect_managers_to_start_screen(
            navigation_manager=self.navigation_manager,
            task_manager=self.task_manager
        )

        self._init_home_screen()
        self._build_home_screen()

        self._init_communication_manager()
        self._init_audio_manager()

        self._init_new_task_screen()
        self._init_settings_screen()

        self._init_select_date_screen()
        self._init_select_alarm_screen()
        self._init_saved_alarm_screen()

        self._init_service_permissions()
    
    ###############################################
    ################### EVENTS ####################
    def on_stop(self):
        super().on_stop()
        logger.debug("App is stopping")
    
    def on_pause(self):
        super().on_pause()
        logger.debug("App is pausing")
        return True
    
    def on_start(self):
        """
        Called after StartScreen's pre_enter.
        - Checks SharedPreferences for actions send while App was closed
        """
        super().on_start()
        print("ON START ON START ON START ON START ON START ON START")

        self._check_start_actions()
    
    def on_resume(self):
        """
        App is resumed from a paused state.
        - Reloads TaskManager's Tasks and Screens UI
        """
        super().on_resume()
        logger.debug("App is resuming")

        if hasattr(self, "task_manager"):
            self._reload_tasks_and_ui()
    
    ###############################################
    ################### MISC ######################
    @log_time("ServicePermissions")
    def _init_service_permissions(self):
        from src.managers.permission_manager import PM
        PM.validate_permission(PM.POST_NOTIFICATIONS)
        PM.validate_permission(PM.REQUEST_SCHEDULE_EXACT_ALARM)
        PM.validate_permission(PM.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
    
    def _build_home_screen(self):
        self.get_screen(SCREEN.HOME)._full_rebuild_task_display()
    
    def _connect_managers_to_start_screen(self, navigation_manager, task_manager):
        self.get_screen(SCREEN.START).navigation_manager = navigation_manager
        self.get_screen(SCREEN.START).task_manager = task_manager
    
    def _reload_tasks_and_ui(self) -> None:
        """Reloads TaskManager's Tasks and Screens UI."""
        self.task_manager.tasks_by_date = self.task_manager._load_tasks_by_date()
        self.get_screen(SCREEN.HOME)._full_rebuild_task_display()
    
    def _check_start_actions(self) -> None:
        """
        Checks SharedPreferences for actions send while App was closed.
        - Show Task Popup
        """
        # Check need show Task popup
        task_id = self.preference_manager.get_and_delete_preference(
            pref_type=DM.PREFERENCE_TYPE.ACTIONS,
            key=DM.PREFERENCE.SHOW_TASK_POPUP
        )
        if task_id:
            print("Found pending Task popup action, waiting for PopupManager...")
            self._wait_for_popup_system(task_id)

    def _wait_for_popup_system(self, task_id: str) -> None:
        """
        Polls every 0.2 seconds until PopupManager is ready.
        Then handles the Task popup.
        """
        def check_popup_ready(dt):
            if not DM.LOADED.POPUP_MANAGER:
                # Not ready, schedule another check
                print("PopupManager not ready, waiting...")
                Clock.schedule_once(check_popup_ready, 0.2)
            else:
                # Ready, handle the popup
                print("PopupManager ready, showing Task popup...")
                self._handle_show_task_popup(task_id)
        
        # Start the polling
        Clock.schedule_once(check_popup_ready, 0)

    def _handle_show_task_popup(self, task_id: str) -> None:
        """Handles showing the Task popup."""
        try:
            task = self.task_manager.expiry_manager._search_expired_task(task_id)
            if task:
                logger.debug(f"Showing popup from SharedPreferences: {DM.get_task_log(task)}")
                self.task_manager.expiry_manager.dispatch(
                    "on_task_expired_show_task_popup",
                    task=task
                )
            else:
                logger.error(f"Error showing Task popup, no Task found for: {DM.get_task_id_log(task_id)}")
            
        except Exception as e:
            logger.error(f"Error showing Task popup: {e}")
    
    ###############################################
    ################### MANAGERS ##################
    @log_time("PreferenceManager")
    def _init_preference_manager(self):
        from src.managers.app_preference_manager import AppPreferencesManager
        self.preference_manager = AppPreferencesManager()
        DM.LOADED.PREFERENCE_MANAGER = True
    
    @log_time("NavigationManager")
    def _init_navigation_manager(self):
        from src.managers.navigation_manager import NavigationManager
        self.navigation_manager = NavigationManager(
            screen_manager=self.screen_manager,
            start_screen=SCREEN.HOME
        )
        DM.LOADED.NAVIGATION_MANAGER = True
    
    @log_time("TaskManager")
    def _init_task_manager(self):
        from src.managers.app_task_manager import TaskManager
        self.task_manager = TaskManager()
        start_screen = self.get_screen(SCREEN.START)
        start_screen._init_task_manager(self.task_manager)
        DM.LOADED.TASK_MANAGER = True
    
    @log_time("CommunicationManager")
    def _init_communication_manager(self):
        from src.managers.app_communication_manager import AppCommunicationManager
        self.communication_manager = AppCommunicationManager(self.task_manager,
                                                             self.task_manager.expiry_manager)
        self.task_manager.communication_manager = self.communication_manager
        DM.LOADED.COMMUNICATION_MANAGER = True
    
    @log_time("AudioManager")
    def _init_audio_manager(self):
        from src.managers.app_audio_manager import AppAudioManager
        self.audio_manager = AppAudioManager()
        DM.LOADED.AUDIO_MANAGER = True
    
    ###############################################
    ################### SCREENS ###################
    @log_time("StartScreen")
    def _init_start_screen(self):
        from src.screens.start.start_screen import StartScreen
        self.screens = {
            SCREEN.START: StartScreen(name=SCREEN.START)
        }
        self.screen_manager.add_widget(self.screens[SCREEN.START])
        DM.LOADED.START_SCREEN = True
    
    @log_time("HomeScreen")
    def _init_home_screen(self):
        from src.screens.home.home_screen import HomeScreen
        self.screens[SCREEN.HOME] = HomeScreen(name=SCREEN.HOME,
                                               navigation_manager=self.navigation_manager,
                                               task_manager=self.task_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.HOME])
        DM.LOADED.HOME_SCREEN = True

    @log_time("NewTaskScreen")
    def _init_new_task_screen(self):
        from src.screens.new_task.new_task_screen import NewTaskScreen
        self.screens[SCREEN.NEW_TASK] = NewTaskScreen(name=SCREEN.NEW_TASK,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager,
                                                    audio_manager=self.audio_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.NEW_TASK])
        DM.LOADED.NEW_TASK_SCREEN = True
    
    @log_time("SettingsScreen")
    def _init_settings_screen(self):
        from src.screens.settings.settings_screen import SettingsScreen
        self.screens[SCREEN.SETTINGS] = SettingsScreen(name=SCREEN.SETTINGS,
                                                    navigation_manager=self.navigation_manager,
                                                    task_manager=self.task_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SETTINGS])
        DM.LOADED.SETTINGS_SCREEN = True

    @log_time("SelectDateScreen")
    def _init_select_date_screen(self):
        from src.screens.select_date.select_date_screen import SelectDateScreen
        self.screens[SCREEN.SELECT_DATE] = SelectDateScreen(name=SCREEN.SELECT_DATE,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_DATE])
        DM.LOADED.SELECT_DATE_SCREEN = True
    
    @log_time("SelectAlarmScreen")
    def _init_select_alarm_screen(self):
        from src.screens.select_alarm.select_alarm_screen import SelectAlarmScreen
        self.screens[SCREEN.SELECT_ALARM] = SelectAlarmScreen(name=SCREEN.SELECT_ALARM,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=self.audio_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SELECT_ALARM])
        DM.LOADED.SELECT_ALARM_SCREEN = True
    
    @log_time("SavedAlarmScreen")
    def _init_saved_alarm_screen(self):
        from src.screens.saved_alarm.saved_alarm_screen import SavedAlarmScreen
        self.screens[SCREEN.SAVED_ALARMS] = SavedAlarmScreen(name=SCREEN.SAVED_ALARMS,
                                                            navigation_manager=self.navigation_manager,
                                                            task_manager=self.task_manager,
                                                            audio_manager=self.audio_manager)
        self.screen_manager.add_widget(self.screens[SCREEN.SAVED_ALARMS])
        DM.LOADED.SAVED_ALARMS_SCREEN = True


if __name__ == "__main__":
    TaskApp().run()
