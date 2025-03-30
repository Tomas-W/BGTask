from kivy.app import App

from src.settings import SCREEN


class NavigationManager:
    """
    NavigationManager is a class that manages the navigation from and to screens.
    """
    def __init__(self, screen_manager, start_screen: str):
        self.screen_manager = screen_manager
        self.history: list[str] = [start_screen]
    
    def _set_slide_directionn(self, slide_direction: str) -> None:
        self.screen_manager.transition.direction = slide_direction
    
    def navigate_to(self, screen_name: str, slide_direction: str = "right", *args) -> None:
        """Navigate TO a screen."""
        if not self._check_is_home_screen(screen_name):
            self.history.append(screen_name)
        else:
            self.history = [SCREEN.HOME]
        
        self._set_slide_directionn(slide_direction)
        self.screen_manager.current = screen_name
    
    def navigate_back_to(self, screen_name: str, slide_direction: str = "left", *args) -> None:
        """Navigate BACK TO a screen."""
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

    def exit_app(self, *args) -> None:
        App.get_running_app().stop()
    
    def _check_is_home_screen(self, screen: str | None = None) -> bool:
        """
        Check if the current screen is the home screen.
        If so, reset the history.
        """
        screen = screen if screen else self.screen_manager.current
        if screen != SCREEN.HOME:
            return False
        
        return True
    
    def go_to_home_screen(self, *args) -> None:
        self.navigate_to(SCREEN.HOME)
    
    def go_to_new_task_screen(self, *args) -> None:
        self.navigate_to(SCREEN.NEW_TASK)
    
    def go_to_select_date_screen(self, *args) -> None:
        self.navigate_to(SCREEN.SELECT_DATE)
    
    def go_to_select_alarm_screen(self, *args) -> None:
        self.navigate_to(SCREEN.SELECT_ALARM)
    
    def go_to_saved_alarms_screen(self, *args) -> None:
        self.navigate_to(SCREEN.SAVED_ALARMS)
    
    def go_to_settings_screen(self, *args) -> None:
        self.navigate_to(SCREEN.SETTINGS)
