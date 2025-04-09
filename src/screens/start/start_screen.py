import json
import os
from functools import lru_cache

from datetime import datetime, timedelta

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from src.widgets.buttons import CustomConfirmButton

from src.widgets.containers import StartContainer, BaseLayout
from src.screens.home.home_widgets import (TaskHeader, TaskContainer, TaskGroupContainer,
                                           TimeLabel, TaskLabel)
from src.widgets.labels import PartitionHeader
from src.managers.tasks.task_manager_utils import Task

from src.utils.misc import device_is_android, get_storage_path, get_task_header_text

from src.settings import DIR, PATH, SCREEN, STATE

import time as time_
from src.utils.logger import logger


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
        self.start_screen_loaded: bool = False
        self.home_screen_ready: bool = False

        self.current_task_data: list[dict] = []
        self.task_date: str = ""

        self.root_layout = FloatLayout()

        self.layout = BaseLayout()

        self.start_container = StartContainer(parent_screen=self)

        self.layout.add_widget(self.start_container)
        self.root_layout.add_widget(self.layout)

        self.add_widget(self.root_layout)

        self.bottom_bar = None

        end_time = time_.time()
        logger.error(f"Start screen init time: {end_time - start_time}")
    
    def _build_page(self) -> None:
        start_time = time_.time()
        self.screen_header = PartitionHeader(text="<< swipe to continue >>")
        self.start_container.container.add_widget(self.screen_header)

        self.task_group = BoxLayout(orientation="vertical", size_hint_y=None)
        self.task_group.bind(minimum_height=self.task_group.setter("height"))

        self.day_header = TaskHeader(text=self.task_date)
        self.task_group.add_widget(self.day_header)

        self.tasks_container = TaskGroupContainer()
        self.task_group.add_widget(self.tasks_container)

        self.start_container.container.add_widget(self.task_group)
        self.screenshot_button = CustomConfirmButton(text="Set as Wallpaper", width=1,
                                                     color_state=STATE.ACTIVE)
        self.screenshot_button.bind(on_release=self.take_screenshot)
        self.start_container.container.add_widget(self.screenshot_button)
        end_time = time_.time()
        logger.error(f"_build_page time: {end_time - start_time}")

    def _load_current_tasks_widgets(self) -> None:
        """
        Loads the tasks widgets into the tasks container.
        These contain the next tasks that are expiring, grouped by date.
        """
        start_time = time_.time()
        self.tasks_container.clear_widgets()
        for task in self.current_task_data:
            task_container = TaskContainer()

            from src.managers.tasks.task_manager_utils import Task
            time = Task.to_time_str(task["timestamp"])
            start_time_label = TimeLabel(text=time)
            task_container.add_widget(start_time_label)

            task_message = TaskLabel(text=task["message"])
            
            def update_text_size(instance, value):
                width = value[0]
                instance.text_size = (width, None)                
                instance.texture_update()
                instance.height = instance.texture_size[1]
                task_container.height = start_time_label.height + instance.height
            
            task_message.bind(size=update_text_size)
            
            task_container.add_widget(task_message)
            self.tasks_container.add_widget(task_container)

        end_time = time_.time()
        logger.error(f"_load_current_tasks_widgets time: {end_time - start_time}")

    def _get_current_task_data(self) -> list[dict]:
        """
        Gets the current task data to display on the StartScreen.
        Priority order:
        1. Today's tasks
        2. The earliest future tasks if no today's tasks exist
        3. Empty list if no future tasks exist
        """
        try:
            today = datetime.now().date()
            today_key = today.isoformat()
            
            if hasattr(self, "task_manager"):
                task_data = []
                # Get all date keys and sort them chronologically
                date_keys = sorted(self.task_manager.tasks_by_date.keys())
                if not date_keys:
                    return []
                
                # Find today or the earliest future date
                target_date_key = None                
                # First check for today's tasks
                if today_key in date_keys and self.task_manager.tasks_by_date[today_key]:
                    target_date_key = today_key
                else:
                    # Find the earliest future date
                    future_dates = [dk for dk in date_keys if dk >= today_key]
                    if future_dates:
                        target_date_key = min(future_dates)
                
                # If we found a suitable date, get its tasks
                if target_date_key:
                    tasks = self.task_manager.tasks_by_date[target_date_key]
                    task_data = [task.to_dict() for task in sorted(tasks, key=lambda t: t.timestamp)]
            
            else:
                # No task manager available, try to read from file
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
            
            return task_data
            
        except Exception as e:
            logger.error(f"Error getting current task data: {e}")
            return []
    
    @property
    def is_completed(self) -> bool:
        return self.start_screen_loaded

    @is_completed.setter
    def is_completed(self, value: bool) -> None:
        """
        Sets the start screen loaded to the value.
        Triggers loading the rest of the app in the background.
        """
        self.start_screen_loaded = value
        from kivy.clock import Clock
        Clock.schedule_once(self.background_load_app_components, 0.1)

    def background_load_app_components(self, dt: float) -> None:
        from kivy.clock import Clock
        def load(dt):
            from kivy.app import App
            App.get_running_app()._load_app_components()
            self.navigation_manager = App.get_running_app().navigation_manager
            Clock.schedule_once(lambda dt: App.get_running_app().get_screen(SCREEN.HOME).update_task_display(), 0.2)
            self.task_manager = App.get_running_app().task_manager
        
        Clock.schedule_once(load, 0.1)

    def on_pre_enter(self) -> None:
        """
        When the screen is about to be shown, the data is loaded in and 
         the widgets are built.
        """
        if not self.start_screen_loaded:
            self._build_page()
        
        self.current_task_data = self._get_current_task_data()
        if self.current_task_data:
            # Get the date from the first task to display in the header
            first_date = self.current_task_data[0]["date"]
            header_text = get_task_header_text(first_date)
            self.day_header.text = header_text
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
        if not self.start_screen_loaded:
            import time
            self.on_enter_time = time.time()        
            self.is_completed = True
            finish_time = time.time()
            from kivy.app import App
            app = App.get_running_app()
            logger.warning(f"TOTAL TIME TO FIRST FRAME: {finish_time - app.start_time}")

    def navigate_to_home_screen(self, slide_direction: str):
        if not self.home_screen_ready:
            from src.utils.logger import logger
            logger.error("Home screen not ready - cannot navigate to it")
            return
        
        self.navigation_manager.navigate_to(SCREEN.HOME, slide_direction)

    def take_screenshot(self, *args) -> None:
        start_time = time_.time()
        try:
            import os
            print("Starting screenshot capture process...")
            
            # Check and request permissions
            if device_is_android():
                try:
                    from android.permissions import request_permissions, Permission, check_permission  # type: ignore
                    if not check_permission(Permission.SET_WALLPAPER):
                        request_permissions([Permission.SET_WALLPAPER])
                    else:
                        print("SET_WALLPAPER permission already granted")
                except Exception as e:
                    print(f"Error requesting permissions: {str(e)}")
            
            # Hide widgets from screenshot
            self.screen_header.opacity = 0
            self.screenshot_button.opacity = 0
                    
            # Take screenshot
            texture = self.root_layout.export_as_image()
            print(f"Screenshot captured as texture type: {type(texture)}")
            
            # Restore visibility

            self.screen_header.opacity = 1
            self.screenshot_button.opacity = 1
            
            if device_is_android():
                start_time = time_.time()
                from android.storage import app_storage_path  # type: ignore
                screenshot_path = os.path.join(app_storage_path(), DIR.IMG, "bgtask_screenshot.png")
            else:
                screenshot_path = os.path.join(DIR.IMG, "bgtask_screenshot.png")
            
            print(f"Saving screenshot to: {screenshot_path}")
            
            # Save the texture
            texture.save(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            logger.error(f"take_screenshot time: {time_.time() - start_time}")
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
                    print(f"Bitmap created successfully, size: {bitmap.getWidth()}x{bitmap.getHeight()}")
                    # Get the WallpaperManager and set the bitmap
                    WallpaperManager = autoclass('android.app.WallpaperManager')
                    manager = WallpaperManager.getInstance(context)
                    manager.setBitmap(bitmap)
                    print("Wallpaper set successfully using bitmap!")
                    logger.error(f"set_wallpaper time: {time_.time() - start_time}")
                else:
                    print("Failed to create bitmap from file")
            else:
                print("Wallpaper functionality is only available on Android.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error during screenshot/wallpaper process: {str(e)}")
        end_time = time_.time()
        logger.error(f"take_screenshot time: {end_time - start_time}")
