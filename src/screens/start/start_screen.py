import time

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.relativelayout import RelativeLayout

from managers.tasks.task import Task, TaskGroup
from managers.device.device_manager import DM

from .start_screen_utils import set_screen_as_wallpaper

from src.widgets.containers import StartContainer, BaseLayout
from src.widgets.buttons import CustomButton
from src.widgets.labels import PartitionHeader
from src.screens.home.home_widgets import TaskGroupWidget

from src.utils.wrappers import android_only
from src.utils.logger import logger
from src.settings import SCREEN, STATE, TEXT

if TYPE_CHECKING:
    from main import TaskApp
    from src.managers.navigation_manager import NavigationManager
    from src.managers.app_task_manager import TaskManager


class StartScreen(Screen):
    """
    StartScreen is the first screen that is shown when the app is opened.
    It is a placeholder displaying the nearest expiring task while the app is loading.
    """
    def __init__(self, app: "TaskApp", **kwargs):
        """
        Background is loaded and displayed.
        When the screen is shown, the page is built and the data is loaded in.
        """
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager

        self._start_screen_finished: bool = False
        self.is_taking_screenshot: bool = False

        self.task_group_widget = None  # Track TaskGroup widget

        # Layout
        self.root_layout = RelativeLayout()
        self.layout = BaseLayout()

        # StartContainer
        self.start_container = StartContainer(parent_screen=self)

        # Screen header
        self.screen_header = PartitionHeader(text="<< swipe to continue >>")
        self.start_container.container.add_widget(self.screen_header)

        # Screenshot button
        self.screenshot_button = CustomButton(text="Set as Wallpaper", width=1,
                                                     color_state=STATE.ACTIVE)
        self.screenshot_button.bind(on_release=self._set_screen_as_wallpaper)
        # Add to container
        self.start_container.container.add_widget(self.screenshot_button)

        # Layout
        self.layout.add_widget(self.start_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

        self.bottom_bar = None

    def _connect_task_manager(self, task_manager) -> None:
        """
        Initializes the TaskManager.
        """
        self.task_manager = task_manager
        
    def refresh_start_screen(self) -> None:
        """
        Updates the Task widgets using the TaskGroup widget.
        Uses the earliest future TaskGroup.
        """
        start_time = time.time()
        # Remove existing TaskGroup widget
        if self.task_group_widget:
            self.start_container.container.remove_widget(self.task_group_widget)
        
        current_task_group = self._get_start_task_group()        
        if not current_task_group:
            # Create default Task
            start_task = Task(timestamp=(datetime.now() - timedelta(minutes=1)).replace(second=0, microsecond=0),
                             message=TEXT.NO_TASKS,
                             expired=True)
            
            # Create TaskGroup
            self.task_group_widget = TaskGroupWidget(
                date_str=start_task.get_date_key(),
                tasks=[start_task],
                task_manager=self.task_manager,
                parent_screen=self,
                clickable=False
            )
        else:
            # Create TaskGroup widget
            self.task_group_widget = TaskGroupWidget(
                date_str=current_task_group.date_str,
                tasks=current_task_group.tasks,
                task_manager=self.task_manager,
                parent_screen=self,
                clickable=False
            )
        
        # Insert between header and screenshot button
        self.start_container.container.add_widget(self.task_group_widget, index=1)
        logger.info(f"Refreshing start screen took: {round(time.time() - start_time, 6)} seconds")
    
    def _get_start_task_group(self) -> TaskGroup:
        """
        Gets the earliest future TaskGroup (including today).
        Returns None if no future tasks exist.
        """
        if not self.task_manager.task_groups:
            return None
        
        today_key = datetime.now().date().isoformat()
        # Find earliest future TaskGroup
        for task_group in self.task_manager.task_groups:
            if task_group.date_str >= today_key:
                return task_group
        
        return None

    @property
    def start_screen_finished(self) -> bool:
        return self._start_screen_finished

    @start_screen_finished.setter
    def start_screen_finished(self, value: bool) -> None:
        """
        Sets the start_screen_finished to the value.
        Triggers loading the rest of the app in the background.
        """
        if self._start_screen_finished == value:
            return
        
        self._start_screen_finished = value
        Clock.schedule_once(self.app.load_app, 0.05)

    def on_pre_enter(self) -> None:
        """
        When the screen is about to be shown, the data is loaded in and 
         the widgets are built.
        """
        if not self._start_screen_finished:
            # Load widgets
            self.refresh_start_screen()

    def _refresh_start_screen(self, *args, **kwargs) -> None:
        """
        Re-loads the StartScreen.
        """
        Clock.schedule_once(lambda dt: self.refresh_start_screen(), 0)
    
    @android_only
    def _hide_loading_screen(self) -> None:
        """
        Hides the loading screen if on Android.
        """
        from android import loadingscreen  # type: ignore
        loadingscreen.hide_loading_screen()

    def on_enter(self) -> None:
        """
        When the screen is shown, the rest of the app is loaded in the background.
        After loading the app, the HomeScreen is loaded.
        """
        if not self._start_screen_finished:
            self.start_screen_finished = True
            
            self._hide_loading_screen()
            
            from src.utils.timer import TIMER
            TIMER.stop("start")
            TIMER.stop("start_app")
            logger.info(TIMER.get_time("start"))
            logger.info(TIMER.get_time("start_app"))
            
            Clock.schedule_once(self.check_need_to_start_service, 0.1)
    
    def check_need_to_start_service(self, dt: float) -> None:
        """
        Checks if the service needs to be started.
        """
        # Only start service if not already running
        from kivy.utils import platform
        if platform == "android":
            from src.utils.background_service import is_service_running
            if not is_service_running():
                from src.utils.background_service import start_background_service
                start_background_service()
                logger.debug("Service started")
            else:
                logger.debug("Service already running")
        
        
    def navigate_to_home_screen(self, slide_direction: str):
        if not DM.LOADED.HOME_SCREEN:
            from src.utils.logger import logger
            logger.error("Home screen not ready - cannot navigate to it")
            return
        
        self.navigation_manager.navigate_to(SCREEN.HOME, slide_direction)

    def _set_screen_as_wallpaper(self, instance) -> None:
        """
        Takes a screenshot of the current screen and,
          if android, sets it as the wallpaper.
        Widgets besides the TaskHeader and TaskGroupContainer are hidden
        while the screenshot is taken.
        """
        # Prevent multiple simultaneous screenshot attempts
        if self.is_taking_screenshot:
            return
            
        self.is_taking_screenshot = True
        
        # Disable the button at UI level to give immediate visual feedback
        self.screenshot_button.disabled = True
        
        # Call the actual screenshot function
        set_screen_as_wallpaper(self.root_layout, self.screen_header, self.screenshot_button)
        
        # Reset the flag when the screenshot process completes
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self, 'is_taking_screenshot', False), 1)
