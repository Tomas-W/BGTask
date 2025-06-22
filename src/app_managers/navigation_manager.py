from typing import TYPE_CHECKING

from managers.device.device_manager import DM
from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp
    from kivy.uix.screenmanager import ScreenManager


class NavigationManager:
    """
    Manages the navigation from and to screens.
    Keeps track of the history of screens.
    Default animation:
    - Going to a screen - slide_direction = "right"
    - Going back - slide_direction = "left"
    """
    def __init__(self, app: "TaskApp", start_screen: str):
        self.app = app
        self.screen_manager: "ScreenManager" = app.screen_manager
        self.history: list[str] = [start_screen]
    
    def _set_slide_direction(self, slide_direction: str) -> None:
        self.screen_manager.transition.direction = slide_direction
    
    def navigate_to(self, screen_name: str, slide_direction: str = "right", *args) -> None:
        """Navigate TO a screen."""
        previous_screen = self.screen_manager.current
        # Don't add if same screen
        if screen_name == previous_screen:
            return
        
        # Remove history after current
        self._remove_history(screen_name)

        # Add to history
        if self._check_is_home_screen(screen_name):
            self.history = [DM.SCREEN.HOME]
        else:
            self.history.append(screen_name)
        
        # Go to screen
        self._set_slide_direction(slide_direction)
        self.screen_manager.current = screen_name
        logger.info(f"history: {self.history}")
    
    def navigate_back_to(self, screen_name: str, slide_direction: str = "left", *args) -> None:
        """Navigate BACK TO a screen."""
        # Remove history after current
        self._remove_history(screen_name)
        
        # Go to screen
        self._set_slide_direction(slide_direction)
        self.screen_manager.current = screen_name
        logger.info(f"history: {self.history}")
    
    def go_back(self, slide_direction: str = "left", *args) -> None:
        """Go back to the previous screen."""
        # Remove last screen
        if len(self.history) > 1:
            self.history.pop()
        
            # Go to screen
            previous = self.history[-1]
            if self._check_is_home_screen(previous): 
                self.history = [DM.SCREEN.HOME]
            
            self._set_slide_direction(slide_direction)
            self.screen_manager.current = previous
        
        logger.info(f"history: {self.history}")

    
    def _check_is_home_screen(self, screen: str | None = None) -> bool:
        """
        Check if the current screen is the home screen.
        If so, reset the history.
        """
        screen = screen if screen else self.screen_manager.current
        if screen != DM.SCREEN.HOME:
            return False
        
        return True

    def _remove_history(self, screen_name: str | None = None) -> None:
        """Removes all history or history after current, if current is provided"""
        if screen_name:
            for i, screen in enumerate(self.history):
                if screen == screen_name:
                    self.history = self.history[:i]
                    break
        else:
            self.history = []

    def exit_app(self, *args) -> None:
        self.app.stop()
