import time as time_
start_time = time_.time()

import json
import os

from datetime import datetime, timedelta

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.relativelayout import RelativeLayout
from src.widgets.buttons import CustomButton

from managers.tasks.task_manager_utils import Task
from managers.device.device_manager import DM

from .start_screen_utils import set_screen_as_wallpaper

from src.widgets.containers import StartContainer, BaseLayout
from src.screens.home.home_widgets import (TaskHeader, TaskContainer, TaskGroupContainer,
                                           TimeContainer, TimeLabel, TaskLabel, TaskIcon)
from src.widgets.labels import PartitionHeader

from src.utils.misc import get_task_header_text

from src.settings import SCREEN, STATE, LOADED, TEXT


from src.utils.logger import logger
logger.error(f"StartScreen IMPORTS time: {time_.time() - start_time:.4f}")



class StartScreen(Screen):
    """
    StartScreen is the first screen that is shown when the app is opened.
    It is a placeholder displaying the nearest expiring task while the app is loading.
    """
    def __init__(self, **kwargs):
        """
        Background is loaded and displayed.
        When the screen is shown, the page is built and the data is loaded in.
        """
        super().__init__(**kwargs)
        start_time = time_.time()
        self._start_screen_finished: bool = False
        self.is_taking_screenshot: bool = False  # Flag to prevent multiple screenshot calls

        self.current_task_data: list[dict] = []
        self.task_date: str = ""

        self.bind(on_task_edit_refresh_start_screen=self._refresh_start_screen)

        # Layout
        self.root_layout = RelativeLayout()
        self.layout = BaseLayout()

        # StartContainer
        self.start_container = StartContainer(parent_screen=self)

        # Screen header
        self.screen_header = PartitionHeader(text="<< swipe to continue >>")
        self.start_container.container.add_widget(self.screen_header)

        # TaskGroup
        self.task_group = BoxLayout(orientation="vertical", size_hint_y=None)
        self.task_group.bind(minimum_height=self.task_group.setter("height"))
        # TaskHeader
        self.day_header = TaskHeader(text=self.task_date)
        self.task_group.add_widget(self.day_header)
        # TaskGroupContainer
        self.tasks_container = TaskGroupContainer()
        self.task_group.add_widget(self.tasks_container)
        # Add to container
        self.start_container.container.add_widget(self.task_group)

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

        end_time = time_.time()
        logger.error(f"StartScreen __INIT__ TIME: {end_time - start_time:.4f}")
    
    def _init_task_manager(self, task_manager) -> None:
        """
        Initializes the TaskManager.
        """
        self.task_manager = task_manager
        self.task_manager.bind(on_task_edit_refresh_start_screen=self._refresh_start_screen)
    
    def _init_current_task_data(self) -> list[dict]:
        """Loads initial Task data from file when task_manager is not yet available."""
        start_time = time_.time()

        task_file_path = DM.get_storage_path(DM.PATH.TASK_FILE)
        if not os.path.exists(task_file_path):
            logger.error("Task file does not exist.")
            return []

        with open(task_file_path, "r") as f:
            data = json.load(f)
            date_keys = sorted(data.keys())
            if not date_keys:
                return []
        
        task_data = []
        today_key = datetime.now().date().isoformat()

        # Get the earliest future date (including today)
        future_dates = [dk for dk in date_keys if dk >= today_key]
        try:
            target_date_key = min(future_dates)
        
        except ValueError:
            logger.debug("No future dates found")
            start_task = Task(timestamp=(datetime.now() - timedelta(minutes=1)).replace(second=0, microsecond=0),
                              message=TEXT.NO_TASKS,
                              expired=True)
            self.day_header.text = get_task_header_text(start_task.get_date_str())
            return [start_task.to_dict()]

        # Create Task objects and add to list
        for task_json in data[target_date_key]:
            task = Task.to_class(task_json)
            task_data.append(task.to_dict())

        # Set the header text
        if task_data:
            task_date = Task.to_date_str(task_data[0]["timestamp"])
            header_text = get_task_header_text(task_date)
            self.day_header.text = header_text

        logger.error(f"HomeScreen _INIT_CURRENT_TASK_DATA TIME: {time_.time() - start_time:.4f}")
        return task_data
    
    def _get_current_task_data(self) -> list[dict]:
        """
        Gets the current task data from the TaskManager to display on the StartScreen.
        Uses sorted_active_tasks to get the earliest TaskGroup [current].
        """
        earliest_task_group = self.task_manager.sorted_active_tasks[0]
        if earliest_task_group and "tasks" in earliest_task_group:
            self.task_date = earliest_task_group["date"]
            return [task.to_dict() for task in earliest_task_group["tasks"]]
        
        return []
    
    def _load_current_tasks_widgets(self) -> None:
        """
        Updates the Task widgets in the TaskGroupContainer.
        These contain the next tasks that are expiring, within a single day.
        """
        start_time = time_.time()
        # Clear existing Tasks
        self.tasks_container.clear_widgets()
        for task in self.current_task_data:
            # No Task check
            no_task = False
            msg = task["message"]
            if msg == TEXT.NO_TASKS:
                no_task = True
                msg = TEXT.NO_TASKS_SHORT
            
            # TaskContainer
            task_container = TaskContainer()
            
            if not no_task:
                # TimeContainer
                time_container = TimeContainer()
                task_container.add_widget(time_container)
                # TimeLabel
                task_time = task["timestamp"] + timedelta(seconds=task["snooze_time"])
                time = Task.to_time_str(task_time)
                start_time_label = TimeLabel(text=time)
                time_container.add_widget(start_time_label)
                # SoundIcon
                if task["alarm_name"]:
                    sound_icon = TaskIcon(source=DM.PATH.SOUND_IMG)
                    time_container.add_widget(sound_icon)
                # VibrateIcon
                if task["vibrate"]:
                    vibrate_icon = TaskIcon(source=DM.PATH.VIBRATE_IMG)
                    time_container.add_widget(vibrate_icon)
            
            # TaskLabel
            task_message = TaskLabel(text=msg)
            task_container.add_widget(task_message)
            
            # Add to layout
            self.tasks_container.add_widget(task_container)
            
            def update_text_size(instance, value):
                width = value[0]
                instance.text_size = (width, None)                
                instance.texture_update()
                instance.height = instance.texture_size[1]
                if not no_task:
                    task_container.height = start_time_label.height + instance.height
                else:
                    task_container.height = instance.height
            
            task_message.bind(size=update_text_size)
        
        if all(task["expired"] for task in self.current_task_data):
            self.tasks_container.set_expired(True)
        else:
            self.tasks_container.set_expired(False)

        end_time = time_.time()
        logger.error(f"StartScreen _LOAD_CURRENT_TASKS_WIDGETS TIME: {end_time - start_time:.4f}")
    
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
        from kivy.app import App
        app = App.get_running_app()
        app.dispatch("on_start_screen_finished_load_app")

    def on_pre_enter(self) -> None:
        """
        When the screen is about to be shown, the data is loaded in and 
         the widgets are built.
        """
        if not self._start_screen_finished:
            # Load widgets
            self.current_task_data = self._init_current_task_data()
            self._load_current_tasks_widgets()
    
    def _refresh_start_screen(self, *args, **kwargs) -> None:
        """
        Re-loads the StartScreen.
        """
        logger.trace("CALLED _REFRESH_START_SCREEN")
        self.current_task_data = self._init_current_task_data()
        Clock.schedule_once(lambda dt: self._load_current_tasks_widgets(), 0)

    def on_enter(self) -> None:
        """
        When the screen is shown, the rest of the app is loaded in the background.
        After loading the app, the HomeScreen is loaded.
        """
        if not self._start_screen_finished:
            import time
            self.on_enter_time = time.time()        
            self.start_screen_finished = True
            
            if DM.is_android:
                from android import loadingscreen  # type: ignore
                # When you want to hide the splash screen:
                loadingscreen.hide_loading_screen()
            
            finish_time = time.time()
            from kivy.app import App
            app = App.get_running_app()
            kivy_time = app.kivy_time
            total_time = finish_time - app.starting_time
            logger.warning(f"KIVY TIME: {kivy_time:.4f}")
            logger.warning(f"APP FIRST FRAME TIME: {finish_time - app.start_app_time:.4f}")
            logger.warning(f"TOTAL FIRST FRAME TIME: {total_time:.4f}")\
            
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
                logger.critical("Service started")
            else:
                logger.critical("Service already running")
        
        
    def navigate_to_home_screen(self, slide_direction: str):
        if not LOADED.HOME:
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
