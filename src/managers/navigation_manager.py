from typing import TYPE_CHECKING

from src.utils.logger import logger

from src.settings import SCREEN

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
    
    def _set_slide_directionn(self, slide_direction: str) -> None:
        self.screen_manager.transition.direction = slide_direction
    
    def navigate_to(self, screen_name: str, slide_direction: str = "right", *args) -> None:
        """Navigate TO a screen."""
        previous_screen = self.screen_manager.current
        # Don't add if same screen
        if screen_name == previous_screen:
            return
        
        # Add to history
        if not self._check_is_home_screen(screen_name):
            self.history.append(screen_name)
        else:
            self.history = [SCREEN.HOME]
        
        self._set_slide_directionn(slide_direction)
        self.screen_manager.current = screen_name
    
    def navigate_back_to(self, screen_name: str, slide_direction: str = "left", *args) -> None:
        """Navigate BACK TO a screen."""
        self.history.append(screen_name)

        self._set_slide_directionn(slide_direction)
        self.screen_manager.current = screen_name
    
    def go_back(self, slide_direction: str = "left", *args) -> None:
        """Go back to the previous screen."""
        if len(self.history) > 1:
            self.history.pop()

            previous = self.history[-1]
            if self._check_is_home_screen(previous): 
                self.history = [SCREEN.HOME]
            
            self._set_slide_directionn(slide_direction)
            self.screen_manager.current = previous
    
    def _check_is_home_screen(self, screen: str | None = None) -> bool:
        """
        Check if the current screen is the home screen.
        If so, reset the history.
        """
        screen = screen if screen else self.screen_manager.current
        if screen != SCREEN.HOME:
            return False
        
        return True

    def exit_app(self, *args) -> None:
        self.app.stop()
