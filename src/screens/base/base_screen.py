from kivy.uix.screenmanager import Screen

class BaseScreen(Screen):
    """Base screen class that implements common functionality for all screens"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.top_bar_is_expanded = False

    def on_pre_enter(self):
        """Called when the screen is entered"""
        self.top_bar_is_expanded = False
        self.switch_top_bar(instance=None, on_enter=True)

    def switch_top_bar(self, instance, on_enter=False):
        """Handle the clicked options"""
        # Toggle the state first
        if not on_enter:
            self.top_bar_is_expanded = not self.top_bar_is_expanded
        
        # Then update the widgets based on the new state
        if self.top_bar_is_expanded:
            self.layout.clear_widgets()
            self.layout.add_widget(self.top_bar_expanded.top_bar_container)
            self.layout.add_widget(self.scroll_container)
        else:
            self.layout.clear_widgets()
            self.layout.add_widget(self.top_bar.top_bar_container)
            self.layout.add_widget(self.scroll_container)
