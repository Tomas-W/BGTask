from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout

from src.screens.base.base_screen import BaseScreen
from src.screens.home.home_screen_utils import HomeScreenUtils
from src.screens.home.home_widgets import TaskNavigator, SwipeBar

from managers.device.device_manager import DM
from src.utils.timer import TIMER
from src.utils.logger import logger
from src.utils.misc import is_widget_visible
from src.settings import SIZE

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
    - Has swipe bars to indicate if there is a previous or next TaskGroup
    """
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager
        
        # Task selection
        self.selected_task: "Task" | None = None
        self.selected_label: "TaskInfoLabel" | None = None

        # Swiping
        self._touch_start_x: float = 0
        self._touch_start_y: float = 0
        self._swipe_threshold: float = SIZE.SWIPE_THRESHOLD
        self._vertical_threshold: float = SIZE.SWIPE_THRESHOLD * 0.7

        # TopBar
        top_left_callback = self.navigate_to_wallpaper_screen
        top_bar_callback = self.navigate_to_new_task_screen
        self.top_bar.make_home_bar(top_left_callback=top_left_callback,
                                   top_bar_callback=top_bar_callback)
        # TopBarExpanded
        self.top_bar_expanded.make_home_bar(top_left_callback=top_left_callback)
    
    def _construct_home_screen(self, *args) -> None:
        """
        Constructs the HomeScreen.
        """
        Clock.schedule_once(self._load_navigator, 0)
        Clock.schedule_once(self._load_swipe_container, 0)
        Clock.schedule_once(self._init_home_screen, 0)
        Clock.schedule_once(self._load_floating_action_buttons, 0)
    
    def _load_navigator(self, *args) -> None:
        """
        Loads the TaskNavigator.
        """
        self.main_content = BoxLayout(orientation='vertical', size_hint=(1, 1))
        self.swipe_container = RelativeLayout(size_hint=(1, 1))

        # TaskNavigator
        self.task_navigator = TaskNavigator(task_group=self.task_manager.current_task_group,
                                          task_manager=self.task_manager)
        self.main_content.add_widget(self.task_navigator)

    def _load_swipe_container(self, *args) -> None:
        """
        Loads the swipe container.
        """
        # Move ScrollContainer: BaseScreen.layout -> main_content
        self.layout.remove_widget(self.scroll_container)
        self.main_content.add_widget(self.scroll_container)

        # Main content first
        self.swipe_container.add_widget(self.main_content)
        # Feedback bars last
        self.left_swipe_bar = SwipeBar(self.task_manager, is_left=True)
        self.right_swipe_bar = SwipeBar(self.task_manager, is_left=False)
        self.swipe_container.add_widget(self.left_swipe_bar)
        self.swipe_container.add_widget(self.right_swipe_bar)
        # Add swipe container
        self.layout.add_widget(self.swipe_container)

    def _load_floating_action_buttons(self, *args) -> None:
        """
        Loads the floating action buttons.
        """
        # Edit and delete buttons
        self.create_floating_action_buttons()

    def on_pre_enter(self) -> None:
        super().on_pre_enter()
        logger.info("HomeScreen on_pre_enter")
    
    def on_enter(self) -> None:
        super().on_enter()
        logger.info("HomeScreen on_enter")
        TIMER.stop("start_home_screen")
    
    def on_leave(self) -> None:
        super().on_leave()
        
        self._deselect_task()
    
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
        """Reset feedback bars and store touch position."""
        if self.collide_point(*touch.pos):
            self._touch_start_x = touch.x
            self._touch_start_y = touch.y
            # Reset bars
            self.left_swipe_bar.width = 0
            self.right_swipe_bar.width = 0
            touch.ud["was_swiped"] = False  # was_swiped blocks Task selection
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """
        Handles touch movement:
        - If horizontal movement - show swipe bar
        - If vertical movement - let scroll view handle it
        """
        if self.collide_point(*touch.pos):
            # Calculate movement
            swipe_distance_x = abs(touch.x - self._touch_start_x)
            swipe_distance_y = abs(touch.y - self._touch_start_y)
            
            # If horizontal movement - show SwipeBar
            if swipe_distance_x > swipe_distance_y:
                touch.ud["was_swiped"] = True  # was_swiped blocks Task selection
                max_width = self.width * SwipeBar.MAX_WIDTH_HINT
                
                if (touch.x - self._touch_start_x) > 0:
                    # Swiping right - show left bar
                    width = min(swipe_distance_x / 8, max_width)
                    self.left_swipe_bar.width = width
                    self.right_swipe_bar.width = 0
                else:
                    # Swiping left - show right bar
                    width = min(swipe_distance_x / 8, max_width)
                    self.right_swipe_bar.width = width
                    self.left_swipe_bar.width = 0
                return True
            else:
                # Vertical movement - let scroll view handle it
                self.left_swipe_bar.width = 0
                self.right_swipe_bar.width = 0
                return self.scroll_container.on_touch_move(touch)

    def on_touch_up(self, touch):
        """Resets swipe bars and handles swipe."""
        if self.collide_point(*touch.pos):
            # Calculate movement
            swipe_distance_x = touch.x - self._touch_start_x
            swipe_distance_y = abs(touch.y - self._touch_start_y)
            
            # Reset bars
            self.left_swipe_bar.width = 0
            self.right_swipe_bar.width = 0
            
            # Trigger if conditions met
            if (abs(swipe_distance_x) > self._swipe_threshold and 
                swipe_distance_y < abs(swipe_distance_x) * 0.7):
                
                if swipe_distance_x > 0:
                    # Swipe right
                    self.task_manager.go_to_prev_task_group()
                else:
                    # Swipe left
                    self.task_manager.go_to_next_task_group()
                return True
        
        return super().on_touch_up(touch)
