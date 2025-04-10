import time as time_
start_time = time_.time()

import json
import os

from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from src.widgets.buttons import CustomConfirmButton

from src.widgets.containers import StartContainer, BaseLayout
from src.screens.home.home_widgets import (TaskHeader, TaskContainer, TaskGroupContainer,
                                           TimeContainer, TimeLabel, TaskLabel, TaskIcon)
from src.widgets.labels import PartitionHeader
from src.managers.tasks.task_manager_utils import Task

from src.utils.misc import device_is_android, get_storage_path, get_task_header_text

from src.settings import DIR, PATH, SCREEN, STATE, LOADED


from src.utils.logger import logger
logger.error(f"Loading StartScreen IMPORTS time: {time_.time() - start_time:.4f}")



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
        self.screen_is_loaded: bool = False

        self.current_task_data: list[dict] = []
        self.task_date: str = ""
        
        # Layout
        self.root_layout = FloatLayout()
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
        self.screenshot_button = CustomConfirmButton(text="Set as Wallpaper", width=1,
                                                     color_state=STATE.ACTIVE)
        self.screenshot_button.bind(on_release=self.take_screenshot)
        # Add to container
        self.start_container.container.add_widget(self.screenshot_button)

        # Layout
        self.layout.add_widget(self.start_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

        self.bottom_bar = None

        end_time = time_.time()
        logger.error(f"__INIT__ TIME: {end_time - start_time:.4f}")
    
    def _load_current_tasks_widgets(self) -> None:
        """
        Loads the tasks widgets into the tasks container.
        These contain the next tasks that are expiring, grouped by date.
        """
        start_time = time_.time()
        # Clear any existing tasks before adding new ones
        self.tasks_container.clear_widgets()
        
        for task in self.current_task_data:
            # TaskContainer
            task_container = TaskContainer()
            
            # TimeContainer
            time_container = TimeContainer()
            # TimeLabel
            time = Task.to_time_str(task["timestamp"])
            start_time_label = TimeLabel(text=time)
            time_container.add_widget(start_time_label)
            # SoundIcon
            if task["alarm_name"]:
                sound_icon = TaskIcon(source=PATH.SOUND_IMG)
                time_container.add_widget(sound_icon)
            # VibrateIcon
            if task["vibrate"]:
                vibrate_icon = TaskIcon(source=PATH.VIBRATE_IMG)
                time_container.add_widget(vibrate_icon)
            
            # TaskLabel
            task_message = TaskLabel(text=task["message"])
            
            # Add to container
            task_container.add_widget(time_container)
            task_container.add_widget(task_message)
            self.tasks_container.add_widget(task_container)
            
            def update_text_size(instance, value):
                width = value[0]
                instance.text_size = (width, None)                
                instance.texture_update()
                instance.height = instance.texture_size[1]
                task_container.height = start_time_label.height + instance.height
            
            task_message.bind(size=update_text_size)
        
        end_time = time_.time()
        logger.error(f"_LOAD_CURRENT_TASKS_WIDGETS TIME: {end_time - start_time:.4f}")

    def _get_current_task_data(self) -> list[dict]:
        """
        Gets the current task data to display on the StartScreen.
        Priority order:
        1. Today's tasks
        2. The earliest future tasks if no today's tasks exist
        3. Empty list if no future tasks exist
        """
        start_time = time_.time()
        try:
            if hasattr(self, "task_manager"):
                # Use the task_manager's sorted_active_tasks if available
                if not hasattr(self.task_manager, "sorted_active_tasks") or not self.task_manager.sorted_active_tasks:
                    self.task_manager.sort_active_tasks()
                
                if self.task_manager.sorted_active_tasks:
                    # Get the first (earliest) task group
                    earliest_task_group = self.task_manager.sorted_active_tasks[0]
                    if earliest_task_group and "tasks" in earliest_task_group:
                        # Store the date for the header
                        self.task_date = earliest_task_group["date"]
                        # Convert task objects to dictionaries
                        return [task.to_dict() for task in earliest_task_group["tasks"]]
                
                # If no active tasks, return empty list
                return []
            else:
                # No task manager available, try to read from file
                today = datetime.now().date()
                today_key = today.isoformat()
                task_file_path = get_storage_path(PATH.TASK_FILE)
                task_data = []
                
                if os.path.exists(task_file_path):
                    with open(task_file_path, "r") as f:
                        data = json.load(f)
                        # Get all date keys and sort them chronologically
                        date_keys = sorted(data.keys())
                        if not date_keys:
                            return []
                        
                        # Find today or the earliest future date
                        target_date_key = None
                        # First check for today's tasks
                        if today_key in date_keys and data[today_key]:
                            target_date_key = today_key
                        else:
                            # Find the earliest future date
                            future_dates = [dk for dk in date_keys if dk >= today_key]
                            if future_dates:
                                target_date_key = min(future_dates)
                        
                        # If we found a suitable date, get its tasks
                        if target_date_key:
                            for task_json in data[target_date_key]:
                                task = Task.to_class(task_json)
                                task_data.append(task.to_dict())
                
            if not task_data:
                return []
            
            # Process timestamps in task data
            for task in task_data:
                if isinstance(task["timestamp"], str):
                    task_timestamp = datetime.fromisoformat(task["timestamp"])
                    task["timestamp"] = task_timestamp
                    task["date"] = task_timestamp.date()
                else:
                    task["date"] = task["timestamp"].date()
            
            # Sort tasks by time
            task_data.sort(key=lambda t: t["timestamp"])
            
            # Store the date for the header if we have tasks
            if task_data:
                task_date = Task.to_date_str(task_data[0]["timestamp"])
                header_text = get_task_header_text(task_date)
                self.day_header.text = header_text

            logger.error(f"_GET_CURRENT_TASK_DATA TIME: {time_.time() - start_time:.4f}")
            return task_data
            
        except Exception as e:
            logger.error(f"Error getting current task data: {e}")
            return []
    
    @property
    def is_completed(self) -> bool:
        return self.screen_is_loaded

    @is_completed.setter
    def is_completed(self, value: bool) -> None:
        """
        Sets the start screen loaded to the value.
        Triggers loading the rest of the app in the background.
        """
        self.screen_is_loaded = value
        from kivy.clock import Clock
        Clock.schedule_once(self.background_load_app_components, 0.01)

    def background_load_app_components(self, dt: float) -> None:
        from kivy.clock import Clock
        def load(dt):
            from kivy.app import App
            App.get_running_app()._load_app_components()
            self.navigation_manager = App.get_running_app().navigation_manager
            self.task_manager = App.get_running_app().task_manager
        
        Clock.schedule_once(load, 0.1)

    def on_pre_enter(self) -> None:
        """
        When the screen is about to be shown, the data is loaded in and 
         the widgets are built.
        """
        self.current_task_data = self._get_current_task_data()
        if self.current_task_data:
            self._load_current_tasks_widgets()
        else:
            # No tasks to display
            self.day_header.text = "No upcoming tasks"
            self.tasks_container.clear_widgets()

    def on_enter(self) -> None:
        """
        When the screen is shown, the rest of the app is loaded in the background.
        After loading the app, the HomeScreen is loaded.
        """
        if not self.screen_is_loaded:
            import time
            self.on_enter_time = time.time()        
            self.is_completed = True
            finish_time = time.time()
            from kivy.app import App
            app = App.get_running_app()
            total_time = finish_time - app.start_kivy_time
            logger.warning(f"TOTAL TIME TO FIRST FRAME: {total_time:.4f}")
            logger.warning(f"APP TIME TO FIRST FRAME: {total_time - app.total_kivy_time:.4f}")
    
    def navigate_to_home_screen(self, slide_direction: str):
        if not LOADED.HOME:
            from src.utils.logger import logger
            logger.error("Home screen not ready - cannot navigate to it")
            return
        
        self.navigation_manager.navigate_to(SCREEN.HOME, slide_direction)

    def take_screenshot(self, *args) -> None:
        start_time = time_.time()
        try:
            import os
            logger.debug("Starting screenshot capture process...")
            
            # Check and request permissions
            if device_is_android():
                try:
                    from android.permissions import request_permissions, Permission, check_permission  # type: ignore
                    if not check_permission(Permission.SET_WALLPAPER):
                        request_permissions([Permission.SET_WALLPAPER])

                except Exception as e:
                    logger.error(f"Error requesting permissions: {str(e)}")
            
            # Hide widgets from screenshot
            self.screen_header.opacity = 0
            self.screenshot_button.opacity = 0
                    
            # Take screenshot
            texture = self.root_layout.export_as_image()
            
            # Restore visibility

            self.screen_header.opacity = 1
            self.screenshot_button.opacity = 1
            
            if device_is_android():
                start_time = time_.time()
                from android.storage import app_storage_path  # type: ignore
                screenshot_path = os.path.join(app_storage_path(), DIR.IMG, "bgtask_screenshot.png")
            else:
                screenshot_path = os.path.join(DIR.IMG, "bgtask_screenshot.png")
            
            logger.edbug(f"Saving screenshot to: {screenshot_path}")
            
            # Save the texture
            texture.save(screenshot_path)
            logger.error(f"take_screenshot time: {time_.time() - start_time:.4f}")
            # Now set the wallpaper on Android using the bitmap approach
            if device_is_android():
                start_time = time_.time()
                from jnius import autoclass  # type: ignore
                print("Setting wallpaper on Android using bitmap approach...")
                # Get the current activity and context
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity
                context = currentActivity.getApplicationContext()
                
                # Use BitmapFactory to decode the image file
                File = autoclass('java.io.File')
                BitmapFactory = autoclass('android.graphics.BitmapFactory')
                file = File(screenshot_path)
                bitmap = BitmapFactory.decodeFile(file.getAbsolutePath())
                
                if bitmap:
                    # Get the WallpaperManager and set the bitmap
                    WallpaperManager = autoclass('android.app.WallpaperManager')
                    manager = WallpaperManager.getInstance(context)
                    manager.setBitmap(bitmap)
                    logger.error(f"set_wallpaper time: {time_.time() - start_time:.4f}")
                else:
                    logger.debug("Failed to create bitmap from file")
            else:
                logger.debug("Wallpaper functionality is only available on Android.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error during screenshot/wallpaper process: {str(e)}")

        end_time = time_.time()
        logger.error(f"take_screenshot time: {end_time - start_time:.4f}")
