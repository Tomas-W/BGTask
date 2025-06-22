import time

from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen
from src.screens.home.home_widgets import TaskGroupWidget

from managers.wallpaper.wallpaper_manager import WallpaperManager

from src.utils.wrappers import log_time
from src.utils.logger import logger
from src.settings import SPACE

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager
    from src.app_managers.app_task_manager import TaskManager


class WallpaperScreen(BaseScreen):
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
        self.wallpaper_manager: WallpaperManager = WallpaperManager()

        self.is_taking_screenshot: bool = False

        # TopBar - add set wallpaper button on TopBarClosed
        self.top_bar.make_wallpaper_bar(top_left_callback=self.navigation_manager.go_back,
                                        top_bar_callback=self.set_screen_as_wallpaper)

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
        self.top_bar.bar_title.set_text("Setting Wallpaper...")
        
        self.wallpaper_manager.create_wallpaper_from_screen(self.scroll_container.container)

        # Reset TopBar
        Clock.schedule_once(lambda dt: self.top_bar.bar_title.set_text("Set as Wallpaper"), 1)
        # Reset is_taking_screenshot flag
        Clock.schedule_once(lambda dt: setattr(self, 'is_taking_screenshot', False), 1)
