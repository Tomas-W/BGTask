from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen
from src.screens.home.home_screen_utils import HomeScreenUtils

from managers.device.device_manager import DM

from src.screens.home.home_widgets import TaskNavigator
from src.settings import SPACE
from src.utils.wrappers import android_only
from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp
    from src.screens.home.home_widgets import TaskInfoLabel
    from src.managers.navigation_manager import NavigationManager
    from src.managers.app_task_manager import TaskManager
    from managers.tasks.task import Task


class HomeScreen(BaseScreen, HomeScreenUtils):
    """
    HomeScreen is the main screen for the app that:
    - Has a TopBar with options
    - Has a navigation bar for selecting dates
    - Displays a list of Tasks for the selected date
    """
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager

        self._home_screen_finished: bool = False

        # Task selection
        self.selected_task: "Task" | None = None
        self.selected_label: "TaskInfoLabel" | None = None

        # TopBar
        top_bar_callback = self.navigate_to_new_task_screen
        top_left_callback = self.navigate_to_wallpaper_screen
        self.top_bar.make_home_bar(top_left_callback=top_left_callback,
                                   top_bar_callback=top_bar_callback)
        # TopBarExpanded
        self.top_bar_expanded.make_home_bar(top_left_callback=top_left_callback)

        # TaskNavigator
        self.task_navigator = TaskNavigator(task_group=self.task_manager.current_task_group,
                                            task_manager=self.task_manager)
        self.layout.add_widget(self.task_navigator, index=1)

        # Edit padding top
        self.scroll_container.container.padding = [SPACE.SCREEN_PADDING_X, SPACE.SPACE_S]
        
        # Edit and delete buttons
        self.create_floating_action_buttons()

        # Build Screen
        self._init_home_screen()
    
    def on_pre_enter(self) -> None:
        super().on_pre_enter()

    def on_enter(self) -> None:
        super().on_enter()

        if not self._home_screen_finished:
            self._hide_loading_screen()
            Clock.schedule_once(self.app.load_app, 0.15)
            Clock.schedule_once(self.check_need_to_start_service, 0.3)
            self._home_screen_finished = True
    
    def on_leave(self) -> None:
        super().on_leave()
        
        self._deselect_task()
    
    @android_only
    def _hide_loading_screen(self) -> None:
        """
        Hides the loading screen if on Android.
        """
        from android import loadingscreen  # type: ignore
        loadingscreen.hide_loading_screen()
    
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
    
    def _deselect_task(self) -> None:
        """
        Deselects any selected Task and hides the floating buttons.
        """
        if self.selected_task:
            if self.selected_label:
                self.selected_label.set_selected(False)
            
            self.selected_task = None
            self.selected_label = None
            self.hide_floating_buttons()
    
    def navigate_to_new_task_screen(self, *args) -> None:
        """
        Navigates to the NewTaskScreen.
        If the edit/delete icons are visible, toggle them off first.
        Deselects any selected Task.
        """
        if not DM.LOADED.NEW_TASK_SCREEN:
            logger.error("NewTaskScreen not ready - cannot navigate to it")
            return
        
        self._deselect_task()
        self.navigation_manager.navigate_to(DM.SCREEN.NEW_TASK)
    
    def navigate_to_wallpaper_screen(self, instance) -> None:
        """
        Navigates to the WallpaperScreen.
        If the edit/delete icons are visible, toggle them off first.
        Deselects any selected Task.
        """
        if not DM.LOADED.WALLPAPER_SCREEN:
            logger.error("WallpaperScreen not ready - cannot navigate to it")
            return
        
        self._deselect_task()
        self.navigation_manager.navigate_to(DM.SCREEN.WALLPAPER)
