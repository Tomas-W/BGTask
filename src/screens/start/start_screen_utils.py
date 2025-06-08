import time

from kivy.clock import Clock

from managers.device.device_manager import DM
from src.managers.permission_manager import PM
from src.utils.wrappers import android_only
from src.utils.logger import logger


def set_screenshot_button(screenshot_button) -> None:
    """Sets the text and state of the screenshot button."""
    screenshot_button.set_text("Setting Wallpaper...")
    screenshot_button.set_inactive_state()


def reset_screenshot_button(dt, screenshot_button) -> None:
    """Resets the text and state of the screenshot button."""
    screenshot_button.set_text("Set as Wallpaper")
    screenshot_button.set_active_state()


def _set_screenshot_as_wallpaper(dt, root_layout, screen_header, screenshot_button) -> None:
    """
    Checks permissions.
    Takes a screenshot of the current root_layout.
    If device is Android, sets the screenshot as the wallpaper.
    """
    # Check permissions, ask if needed
    if not PM.validate_permission(PM.SET_WALLPAPER):
        Clock.schedule_once(lambda dt: reset_screenshot_button(dt, screenshot_button), 0.5)
        return
    
    # Take screenshot
    screenshot_path = take_screenshot(root_layout, screen_header, screenshot_button)
    
    # Set wallpaper
    if screenshot_path:
        set_wallpaper(screenshot_path)


def set_screen_as_wallpaper(root_layout, screen_header, screenshot_button) -> None:
    """
    If Android, sets the current screen as the wallpaper.
    Otherwise, just takes a screenshot.
    Temporary disable screenshot button.
    """
    set_screenshot_button(screenshot_button)
    Clock.schedule_once(lambda dt: _set_screenshot_as_wallpaper(
        dt,
        root_layout,
        screen_header,
        screenshot_button), 0)
    
    Clock.schedule_once(lambda dt: reset_screenshot_button(dt, screenshot_button), 2)


def take_screenshot(root_layout, screen_header, screenshot_button) -> str:
    """
    Hides widgets except for the TaskHeader and TaskGroupContainer.
    Takes a screenshot of the current root_layout.
    """
    try:
        # Check permissions, ask if needed
        if not PM.validate_permission(PM.SET_WALLPAPER):
            return
        
        start_time = time.time()

        hide_widgets([screen_header, screenshot_button])
        # Take screenshot
        texture = root_layout.export_as_image()
        show_widgets([screen_header, screenshot_button])
        
        screenshot_path = DM.get_storage_path(DM.PATH.SCREENSHOT_PATH)
        # Save screenshot
        texture.save(screenshot_path)
        DM.validate_file(screenshot_path)

        logger.debug(f"take_screenshot time: {time.time() - start_time:.4f}")
        return screenshot_path

    except Exception as e:
        logger.error(f"Error during screenshot/wallpaper process: {str(e)}")
        show_widgets([screen_header, screenshot_button])
        return None


@android_only
def set_wallpaper(screenshot_path: str) -> None:
    """
    Sets the screenshot as the wallpaper.
    """
    start_time = time.time()
    try:
        from jnius import autoclass  # type: ignore
        # Get current activity and context
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        currentActivity = PythonActivity.mActivity
        context = currentActivity.getApplicationContext()
        
        # Decode
        File = autoclass("java.io.File")
        BitmapFactory = autoclass("android.graphics.BitmapFactory")
        file = File(screenshot_path)
        bitmap = BitmapFactory.decodeFile(file.getAbsolutePath())
        
        if bitmap:
            # Get WallpaperManager and set the bitmap
            WallpaperManager = autoclass("android.app.WallpaperManager")
            manager = WallpaperManager.getInstance(context)
            manager.setBitmap(bitmap)
            logger.debug(f"set_wallpaper time: {time.time() - start_time:.4f}")
        else:
            logger.error("Failed to create bitmap from file")
    
    except Exception as e:
        logger.error(f"Error during screenshot/wallpaper process: {str(e)}")


def hide_widgets(widgets: list) -> None:
    """
    Sets the opacity of the widgets to 0.
    """
    for widget in widgets:
        widget.opacity = 0


def show_widgets(widgets: list) -> None:
    """
    Sets the opacity of the widgets to 1.
    """
    for widget in widgets:
        widget.opacity = 1
