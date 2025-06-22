import time

from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen
from src.screens.home.home_widgets import TaskGroupWidget

from managers.wallpaper.wallpaper_manager import WallpaperManager

from src.utils.logger import logger
from src.settings import COL, SPACE

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager
    from src.app_managers.app_task_manager import TaskManager


class WallpaperScreen(BaseScreen):

    MIN_SCREENSHOT_TIME: float = 3.0
    """
    WallpaperScreen is the screen that is shown when the user wants to set
     the active TaskGroup as wallpaper.
    """
    def __init__(self, app: "TaskApp", **kwargs):
        """
        Displays the active TaskGroup and a button to set it as wallpaper.
        """
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager
        self.wallpaper_manager: WallpaperManager = WallpaperManager(self)

        self.is_taking_screenshot: bool = False
        self.screenshot_time: float = 0

        # TopBar - add set wallpaper button on TopBarClosed
        self.top_bar.make_wallpaper_bar(top_bar_callback=self.set_screen_as_wallpaper)

        self.scroll_container.container.padding = [SPACE.SCREEN_PADDING_X, SPACE.SPACE_L]

        # TaskGroupWidget - make sure it is not clickable
        self.task_group = TaskGroupWidget(self.task_manager.current_task_group,
                                          clickable=False)
        self.scroll_container.container.add_widget(self.task_group)

    def on_pre_enter(self) -> None:
        """
        When the screen is about to be shown, the data is loaded in and 
         the widgets are built.
        """
        super().on_pre_enter()
    
    def on_enter(self) -> None:
        """
        When the screen is shown, the rest of the app is loaded in the background.
        After loading the app, the HomeScreen is loaded.
        """
        super().on_enter()

    def refresh_wallpaper_screen(self) -> None:
        """
        Refreshes the screen by removing the current TaskGroupWidget and creating
        a new one with the updated task_manager.current_task_group.
        """
        # Remove the current task group widget
        self.scroll_container.container.remove_widget(self.task_group)
        
        # Create new TaskGroupWidget - make sure it is not clickable
        self.task_group = TaskGroupWidget(self.task_manager.current_task_group,
                                          clickable=False)
        self.scroll_container.container.add_widget(self.task_group)
    
    def set_screen_as_wallpaper(self, instance) -> None:
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
        self.screenshot_time = time.time()
        self._prepare_screen()
        
        self.wallpaper_manager.create_wallpaper_from_screen(self.scroll_container.container)
    
    def _prepare_screen(self) -> None:
        """
        Sets the title of the top bar.
        """
        self.top_bar.bar_title.set_text("Setting Wallpaper...")
        self.top_bar.bar_title.color = COL.TEXT_GREY
    
    def _reset_screen(self, scheduled=False, *args) -> None:
        """
        Resets the title of the top bar.
        Order is important here.
        """
        now = time.time()
        time_elapsed = now - self.screenshot_time
        
        # Setting wallpaper > MIN_SCREENSHOT_TIME
        if time_elapsed > WallpaperScreen.MIN_SCREENSHOT_TIME:
            logger.info("time_elapsed > MIN_SCREENSHOT_TIME")
            # Reset immediately if enough time has passed
            self.top_bar.bar_title.set_text("Set as Wallpaper")
            self.top_bar.bar_title.color = COL.WHITE
            self.is_taking_screenshot = False
        
        # First call
        elif not args:
            extra_time = WallpaperScreen.MIN_SCREENSHOT_TIME - time_elapsed + 0.2  # + buffer
            logger.info(f"Extra time: {extra_time}")
            Clock.schedule_once(lambda dt: self._reset_screen(scheduled=True), extra_time)
        
        # Scheduled with extra time
        elif scheduled:
            logger.info("scheduled")
            self.top_bar.bar_title.set_text("Set as Wallpaper")
            self.top_bar.bar_title.color = COL.WHITE
            self.is_taking_screenshot = False
