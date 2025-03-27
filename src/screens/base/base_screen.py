from kivy.app import App
from kivy.uix.screenmanager import Screen


class BaseScreen(Screen):
    """Base screen class that implements common functionality for all screens"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = App.get_running_app().logger
        self.top_bar_is_expanded = False
    
    def switch_top_bar(self, on_enter=False, *args):
        """Controls the state of the TopBar to be expanded or not"""
        # Toggle the state
        if not on_enter:
            self.top_bar_is_expanded = not self.top_bar_is_expanded
        
        # Update the widgets based on the new state
        if self.top_bar_is_expanded:
            self.layout.clear_widgets()
            self.layout.add_widget(self.top_bar_expanded.top_bar_container)
            self.layout.add_widget(self.scroll_container)
        else:
            self.layout.clear_widgets()
            self.layout.add_widget(self.top_bar.top_bar_container)
            self.layout.add_widget(self.scroll_container)
    
    def set_callback(self, callback):
        """Set the callback function to be called when date is confirmed"""
        self.callback = callback

    def on_pre_enter(self):
        """Called before the screen is entered"""
        self.top_bar_is_expanded = False
        self.switch_top_bar(on_enter=True)
    
    def on_enter(self):
        """Called when the screen is entered"""
        pass    
