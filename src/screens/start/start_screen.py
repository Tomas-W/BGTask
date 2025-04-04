from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from src.widgets.containers import BaseLayout
from src.widgets.buttons import CustomConfirmButton

from src.utils.platform import device_is_android

from src.settings import DIR, PATH, SCREEN, STATE, SPACE


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
        self.start_screen_loaded: bool = False

        self.task_data: list[dict] = []
        self.task_date: str = ""

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)
    
    def _build_page(self):
        """
        Builds the page with the day header and the tasks container.
        """
        from src.widgets.containers import ScrollContainer, Partition
        from src.screens.home.home_widgets import TaskHeader, TaskGroupContainer
        from src.widgets.labels import PartitionHeader

        self.scroll_container = ScrollContainer()

        self.header_partition = Partition()
        self.screen_header = PartitionHeader(text="<< swipe to continue >>")
        self.header_partition.add_widget(self.screen_header)
        self.scroll_container.container.add_widget(self.header_partition)

        self.current_task_partition = Partition()
        self.current_task_partition.spacing = 0
        
        self.day_header = TaskHeader(text=self.task_date)
        self.current_task_partition.add_widget(self.day_header)

        self.tasks_container = TaskGroupContainer()
        self.current_task_partition.add_widget(self.tasks_container)

        self.scroll_container.container.add_widget(self.current_task_partition)

        self.screenshot_partition = Partition()
        self.screenshot_button = CustomConfirmButton(text="Set as Wallpaper", width=1,
                                                     color_state=STATE.ACTIVE)
        self.screenshot_button.bind(on_release=self.take_screenshot)
        self.screenshot_partition.add_widget(self.screenshot_button)
        self.scroll_container.container.add_widget(self.screenshot_partition)

        self.layout.add_widget(self.scroll_container)

    def _load_current_tasks_widgets(self) -> None:
        """
        Loads the tasks widgets into the tasks container.
        These contain the next tasks that are expiring, grouped by date.
        """
        from src.screens.home.home_widgets import (TaskContainer, TaskLabel,
                                                   TimeLabel)
        
        for task in self.task_data:
            task_container = TaskContainer()

            time = task["timestamp"].strftime("%H:%M")
            start_time_label = TimeLabel(text=time)
            start_time_label.padding = [SPACE.FIELD_PADDING_X, 0, 0, 0]
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

    def _get_current_task_data(self) -> list[dict]:
        """
        Gets the current task data from the task file.
        It returns todays Task, or nearest future Task.
        """
        try:
            import json
            import os
            from datetime import datetime
            if os.path.exists(PATH.TASK_FILE):
                with open(PATH.TASK_FILE, "r") as f:
                    task_data = json.load(f)
            else:
                task_data = []
            
            today = datetime.now().date()
            future_tasks = []
            for task in task_data:
                task_timestamp = datetime.fromisoformat(task["timestamp"])
                task_date = task_timestamp.date()
                
                if today <= task_date:
                    task["timestamp"] = task_timestamp
                    task["date"] = task_date
                    future_tasks.append(task)
            
            if not future_tasks:
                return []
            
            future_tasks.sort(key=lambda x: x["timestamp"])
            earliest_date = future_tasks[0]["date"]            
            return [task for task in future_tasks if task["date"] == earliest_date]
            
        except Exception as e:
            raise e
    
    def _load_attributes(self) -> None:
        """
        Loads the attributes of the screen.
        """
        from kivy.app import App
        self.navigation_manager = App.get_running_app().navigation_manager
        
    def reset_start_screen(self, *args) -> None:
        """
        Reloads start screen data.
        """
        self.tasks_container.clear_widgets()
        self.task_data = self._get_current_task_data()
        self._load_current_tasks_widgets()

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
        self.on_is_completed_change()

    def on_is_completed_change(self) -> None:
        """
        When the StartScreen finished loading, the rest of the app is loaded.
        """
        from kivy.clock import Clock
        Clock.schedule_once(self.background_load_app_components, 0.01)

    def background_load_app_components(self, dt: float) -> None:
        from kivy.app import App
        App.get_running_app()._load_app_components()
        self._load_attributes()
    
    def on_pre_enter(self) -> None:
        if self.start_screen_loaded:
            self.reset_start_screen()

    def on_enter(self) -> None:
        """
        When the screen is shown, the page is built and the data is loaded in.
        """
        if not self.start_screen_loaded:
            import time
            self.on_enter_time = time.time()        
            from kivy.clock import Clock
            Clock.schedule_once(self.load_data_background, 0.1)
        
    def load_data_background(self, dt: float) -> None:
        self._build_page()
        self.task_data = self._get_current_task_data()
        
        if self.task_data:
            task_date = self.task_data[0]["timestamp"].date()
            self.day_header.text = task_date.strftime("%A, %B %d, %Y")
            self._load_current_tasks_widgets()
        
        self.is_completed = True

    def on_touch_down(self, touch) -> bool:
        # Store the initial touch position
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch) -> bool:
        # Calculate the distance moved
        delta_x = touch.x - self.touch_start_x
        delta_y = touch.y - self.touch_start_y

        # Determine if the swipe is significant enough
        if abs(delta_x) > 50 or abs(delta_y) > 50:  # Adjust threshold as needed
            if abs(delta_x) > abs(delta_y):  # Horizontal swipe
                if delta_x > 0:
                    self.on_swipe_right()
                else:
                    self.on_swipe_left()
            else:  # Vertical swipe
                if delta_y > 0:
                    self.on_swipe_up()
                else:
                    self.on_swipe_down()

        return super().on_touch_up(touch)

    def on_swipe_right(self) -> None:
        self.navigation_manager.navigate_to(SCREEN.HOME, slide_direction="right")

    def on_swipe_left(self) -> None:
        self.navigation_manager.navigate_to(SCREEN.HOME, slide_direction="left")

    def on_swipe_up(self) -> None:
        pass

    def on_swipe_down(self) -> None:
        pass

    def take_screenshot(self, *args) -> None:
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
            if hasattr(self, "header_partition"):
                header_visible = self.header_partition.opacity > 0
                self.header_partition.opacity = 0
            else:
                header_visible = False
            
            self.screenshot_button.opacity = 0
                        
            # Redraw
            self.root_layout.do_layout()
            
            # Take screenshot
            texture = self.root_layout.export_as_image()
            print(f"Screenshot captured as texture type: {type(texture)}")
            
            # Restore visibility
            if hasattr(self, "header_partition") and header_visible:
                self.header_partition.opacity = 1
            self.screenshot_button.opacity = 1
            
            if device_is_android():
                from android.storage import app_storage_path  # type: ignore
                screenshot_path = os.path.join(app_storage_path(), DIR.IMG, "bgtask_screenshot.png")
            else:
                screenshot_path = os.path.join(DIR.IMG, "bgtask_screenshot.png")
            
            print(f"Saving screenshot to: {screenshot_path}")
            
            # Save the texture
            texture.save(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            # Now set the wallpaper on Android using the bitmap approach
            if device_is_android():
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
                else:
                    print("Failed to create bitmap from file")
            else:
                print("Wallpaper functionality is only available on Android.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error during screenshot/wallpaper process: {str(e)}")
