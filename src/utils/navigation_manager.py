from src.settings import SCREEN


class NavigationManager:
    """
    NavigationManager is a class that manages the navigation from and to screens.
    """
    def __init__(self, screen_manager, start_screen):
        self.screen_manager = screen_manager
        self.history = [start_screen]
       
    def navigate_to(self, screen_name, slide_direction="right"):
        """
        Navigate to a screen.
        """
        if not self.check_is_home_screen(screen_name):
            self.history.append(screen_name)
        else:
            self.history = [SCREEN.HOME]

        self.screen_manager.transition.direction = slide_direction
        self.screen_manager.current = screen_name
       
    def go_back(self, slide_direction="left", *args):
        """
        Go back to the previous screen.
        The *args parameter allows this method to be used as an event handler.
        """
        if len(self.history) > 1:
            self.history.pop()

            previous = self.history[-1]
            if self.check_is_home_screen(previous): 
                self.history = [SCREEN.HOME]
                
            self.screen_manager.transition.direction = slide_direction
            self.screen_manager.current = previous



    def check_is_home_screen(self, screen = None):
        """
        Check if the current screen is the home screen.
        If so, reset the history.
        """
        screen = screen if screen else self.screen_manager.current
        if screen != SCREEN.HOME:
            return False
        
        return True

