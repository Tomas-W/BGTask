import time

from src.managers.device_manager import DM

from src.utils.logger import logger

from src.settings import PATH


def take_screenshot(root_layout, screen_header, screenshot_button) -> None:
        try:           
            if DM.is_android:
                if not DM.has_wallpaper_permission:
                    DM.request_android_wallpaper_permissions()
                    return
            
            start_time = time.time()
            # Hide widgets from screenshot
            screen_header.opacity = 0
            screenshot_button.opacity = 0
            # Take screenshot
            texture = root_layout.export_as_image()
            # Restore visibility
            screen_header.opacity = 1
            screenshot_button.opacity = 1
            
            screenshot_path = DM.get_storage_path(PATH.SCREENSHOT_PATH)
            
            # Save texture
            logger.warning(f"Saving texture to {screenshot_path}")
            texture.save(screenshot_path)
            logger.warning(f"Texture saved to {screenshot_path}")
            DM.validate_file(screenshot_path)
            logger.warning(f"File validated")
            logger.debug(f"take_screenshot time: {time.time() - start_time:.4f}")
            # Set wallpaper
            if DM.is_android:
                start_time = time.time()
                from jnius import autoclass  # type: ignore
                # Get current activity and context
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity
                context = currentActivity.getApplicationContext()
                
                # Decode
                File = autoclass('java.io.File')
                BitmapFactory = autoclass('android.graphics.BitmapFactory')
                file = File(screenshot_path)
                bitmap = BitmapFactory.decodeFile(file.getAbsolutePath())
                
                if bitmap:
                    # Get WallpaperManager and set the bitmap
                    WallpaperManager = autoclass('android.app.WallpaperManager')
                    manager = WallpaperManager.getInstance(context)
                    manager.setBitmap(bitmap)
                    logger.debug(f"set_wallpaper time: {time.time() - start_time:.4f}")
                else:
                    logger.error("Failed to create bitmap from file")
            else:
                logger.debug("Wallpaper functionality is only available on Android.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error during screenshot/wallpaper process: {str(e)}")

        end_time = time.time()
        logger.error(f"take_screenshot time: {end_time - start_time:.4f}")