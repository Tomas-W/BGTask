from typing import TYPE_CHECKING

from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen
from src.screens.home.home_screen_utils import HomeScreenUtils
from src.screens.home.home_widgets import TaskNavigator

from managers.device.device_manager import DM
from src.utils.wrappers import android_only
from src.utils.logger import logger
from src.utils.misc import is_widget_visible
from src.settings import SIZE, SPACE

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager
    from src.app_managers.app_task_manager import TaskManager
    from src.screens.home.home_widgets import TaskGroupWidget, TaskInfoLabel
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
        top_left_callback = self.navigate_to_wallpaper_screen
        top_bar_callback = self.navigate_to_new_task_screen
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

        # Swiping
        self._touch_start_x: float = 0
        self._touch_start_y: float = 0
        self._swipe_threshold: float = SIZE.SWIPE_THRESHOLD
        self._vertical_threshold: float = SIZE.SWIPE_THRESHOLD * 0.8

    def on_pre_enter(self) -> None:
        super().on_pre_enter()

    def on_enter(self) -> None:
        super().on_enter()

        if not self._home_screen_finished:
            self._hide_loading_screen()
            Clock.schedule_once(self.app.load_app, 0.3)
            Clock.schedule_once(self.check_need_to_start_service, 1.0)
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
    
    def scroll_to_pos_on_date(self, pos: float, date: str) -> None:
        """
        Scrolls to the position if the date is the currently displayed TaskGroup.
        """
        if self.task_manager.current_task_group.date_str == date:
            self.scroll_container.scroll_view.scroll_y = pos

    def _get_task_widget(self, task: "Task") -> "TaskInfoLabel | None":
        """
        Returns the TaskInfoLabel widget for a given Task.
        """
        task_group_widget = self._get_current_task_group_widget()
        if not task_group_widget:
            return None
        
        # Find by ID
        for task_info_label in task_group_widget.task_info_container.children:
            if task_info_label.task_id == task.task_id:
                return task_info_label
        
        return None

    def _get_current_task_group_widget(self) -> "TaskGroupWidget | None":
        """Returns the TaskGroupWidget that is being displayed."""
        children = self.scroll_container.container.children
        if children:
            return children[0]  # Should be only one
        
        return None

    def scroll_to_task(self, task: "Task") -> None:
        """
        Scrolls to make the Task visible if it's not already fully visible in the viewport.
        Also highlights the task briefly.
        """
        task_widget = self._get_task_widget(task)
        if not task_widget:
            logger.warning(f"Task widget not found to scroll to for Task {DM.get_task_id_log(task.task_id)}")
            return
        
        # Scroll if not visible
        if not is_widget_visible(task_widget, self.scroll_container.scroll_view):
            self.scroll_container.scroll_view.scroll_to(task_widget, animate=True)
        
        # Highlight
        Clock.schedule_once(lambda dt: self._highlight_task(task_widget), 0.3)
        Clock.schedule_once(lambda dt: self._unhighlight_task(task_widget), 2.5)
    
    def _highlight_task(self, task_widget: "TaskInfoLabel", *args) -> None:
        """
        Highlights the Task.
        """
        if task_widget is not None:
            task_widget.set_selected()
    
    def _unhighlight_task(self, task_widget: "TaskInfoLabel", *args) -> None:
        """
        Unhighlights the Task.
        """
        if task_widget is not None:
            task_widget.set_selected(False)

    def on_touch_down(self, touch):
        """Sets the touch start coordinates for swipe gestures."""
        if self.collide_point(*touch.pos):
            self._touch_start_x = touch.x
            self._touch_start_y = touch.y
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        """
        If swipe_x > swipe_threshold and swipe_y < vertical_threshold,
        go to previous or next TaskGroup.
        """
        if self.collide_point(*touch.pos):
            # Calculate movement
            swipe_distance_x = touch.x - self._touch_start_x
            swipe_distance_y = abs(touch.y - self._touch_start_y)
            
            # Trigger if conditions met
            if (abs(swipe_distance_x) > self._swipe_threshold and 
                swipe_distance_y < self._vertical_threshold):
                
                if swipe_distance_x > 0:
                    # Swipe right
                    self.task_manager.go_to_prev_task_group()
                else:
                    # Swipe left
                    self.task_manager.go_to_next_task_group()
                return True
        
        return super().on_touch_up(touch)
