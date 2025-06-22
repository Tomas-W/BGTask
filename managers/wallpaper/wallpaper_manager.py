from typing import Optional, TYPE_CHECKING
from kivy.clock import Clock
from kivy.core.window import Window
from PIL import Image

from managers.device.device_manager import DM
from src.app_managers.permission_manager import PM

from src.utils.wrappers import android_only, log_time
from src.utils.logger import logger
from src.settings import COL

if TYPE_CHECKING:
    from kivy.uix.boxlayout import BoxLayout


class WallpaperManager:
    """Manages wallpaper functionality including screenshots and setting wallpapers."""
    
    def __init__(self):
        self._is_processing = False
    
    def create_wallpaper_from_screen(self, layout: "BoxLayout") -> None:
        """
        Schedules the wallpaper creation process.
        """
        if self._is_processing:
            logger.warning("Wallpaper creation already in progress")
            return
            
        self._is_processing = True        
        Clock.schedule_once(lambda dt: self._process_wallpaper_creation(dt,
                                                                        layout), 0)
    @log_time("process_wallpaper_creation")
    def _process_wallpaper_creation(self, dt: float, layout: "BoxLayout") -> None:
        """
        Creates a wallpaper from the layout.
        - Captures a screenshot of the layout
        - Scales the image to fit the screen
        - Centers the image on a background canvas
        - Sets the image as wallpaper (Android only)
        """
        logger.trace("Processing wallpaper creation")
        try:
            if not PM.validate_permission(PM.SET_WALLPAPER):
                return
                
            screenshot_path = self._capture_screenshot(layout)
            if not screenshot_path:
                return
                
            self._optimize_image_for_wallpaper(screenshot_path)
            
            # if DM.is_android:
            self._set_android_wallpaper(screenshot_path)
        
        except Exception as e:
            logger.error(f"Error creating wallpaper: {str(e)}")
        finally:
            self._is_processing = False
    
    def _capture_screenshot(self, layout: "BoxLayout") -> Optional[str]:
        """
        Saves a screenshot of the layout to the storage SCREENSHOT_PATH.
        - Ensures the layout is properly sized
        - Captures the image
        - Saves the image to the storage
        - Verifies the file was created
        - Returns the path to the saved image
        """
        try:
            # Force layout to use full screen width
            screen_width, screen_height = map(int, Window.size)
            layout.size_hint = (1, None)  # Use full width
            layout.width = screen_width
            
            # Ensure proper layout
            layout.do_layout()
            
            # Capture the image
            texture = layout.export_as_image()
            
            # Save
            screenshot_path = DM.get_storage_path(DM.PATH.SCREENSHOT_PATH)
            texture.save(screenshot_path)
            
            # Verify
            if not DM.validate_file(screenshot_path):
                logger.error("Error validating screenshot file, aborting")
                return None
            
            logger.trace(f"Screenshot captured: {layout.size} -> {texture.size}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return None
    
    def _optimize_image_for_wallpaper(self, image_path: str) -> None:
        """
        Optimizes the captured image for wallpaper use:
        - Resizes to fit screen dimensions
        - Centers on background canvas
        - Maintains aspect ratio
        """
        try:
            with Image.open(image_path) as img:
                screen_width, screen_height = map(int, Window.size)
                
                # If already screen size, no optimization
                if img.size == (screen_width, screen_height):
                    return
                
                # Create canvas with screen dimensions
                background_color = tuple(int(c * 255) for c in COL.BG[:3])
                background = Image.new("RGB", (screen_width, screen_height), background_color)
                
                # MAke image fit
                scale_x = screen_width / img.width
                scale_y = screen_height / img.height
                scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down if needed
                
                # Resize image
                new_size = (int(img.width * scale), int(img.height * scale))
                resized_img = img.resize(new_size, Image.LANCZOS)
                
                # Center image
                x_offset = (screen_width - new_size[0]) // 2
                y_offset = (screen_height - new_size[1]) // 2
                background.paste(resized_img, (x_offset, y_offset))
                
                # Save
                background.save(image_path)
                logger.trace(f"Image optimized: {img.size} -> {new_size} (screen: {screen_width}x{screen_height})")
                        
        except Exception as e:
            logger.error(f"Error optimizing image: {str(e)}")
    
    @android_only
    def _set_android_wallpaper(self, image_path: str) -> None:
        """
        Sets the image as Android wallpaper using native APIs.
        """
        try:
            from jnius import autoclass  # type: ignore
            
            # Get Android context
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            current_activity = PythonActivity.mActivity
            context = current_activity.getApplicationContext()
            
            # Load image as bitmap
            File = autoclass("java.io.File")
            BitmapFactory = autoclass("android.graphics.BitmapFactory")
            
            file = File(image_path)
            bitmap = BitmapFactory.decodeFile(file.getAbsolutePath())
            
            if not bitmap:
                logger.error("Error creating bitmap from image file")
                return
            
            # Set as wallpaper
            WallpaperManager = autoclass("android.app.WallpaperManager")
            wallpaper_manager = WallpaperManager.getInstance(context)
            wallpaper_manager.setBitmap(bitmap)
            logger.trace("Android wallpaper set")
                    
        except Exception as e:
            logger.error(f"Error setting Android wallpaper: {str(e)}")
