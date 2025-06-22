from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button

from src.widgets.containers import TopBarContainer
from src.widgets.buttons import TopBarTitle, TopBarButton

from src.settings import FONT, COL, SIZE, SPACE
from managers.device.device_manager import DM

class TopBarClosed():
    """
    TopBarClosed is the TopBar of the all screens that:
    - Has a Back button for going back to the previous screen.
    - Has an Options button for showing the options.

    When .make_home_bar() is called:
    - The back button is replaced with an edit button.
    - The bar title is set to a "+".
    - The title will be clickable to open the NewTaskScreen.
    """
    def __init__(self,
                 top_left_callback,
                 options_callback,
                 ):
        self.top_left_callback = top_left_callback

        self.top_bar_container = TopBarContainer()

        self.top_left_button = TopBarButton(img_path=DM.PATH.BACK_IMG, radius_side="right")
        self.top_left_button.bind(on_release=top_left_callback)

        self.bar_title = TopBarTitle(text="")

        self.options_button = TopBarButton(img_path=DM.PATH.OPTIONS_IMG, radius_side="left")
        self.options_button.bind(on_release=options_callback)

        self.top_bar_container.add_widget(self.top_left_button)
        self.top_bar_container.add_widget(self.bar_title)
        self.top_bar_container.add_widget(self.options_button)
    
    def make_home_bar(self, top_left_callback, top_bar_callback):
        """Make the home bar"""
        self.top_left_button.set_image(DM.PATH.SCREENSHOT_IMG)
        self.top_left_button.unbind(on_release=self.top_left_callback)
        self.top_left_button.bind(on_release=top_left_callback)
        self.bar_title.set_symbol_font_size(FONT.TOP_BAR_SYMBOL)
        self.bar_title.set_text("+")
        self.bar_title.set_disabled(False)
        self.bar_title.bind(on_release=top_bar_callback)
    
    def make_wallpaper_bar(self, top_bar_callback):
        """Make the wallpaper bar"""
        self.bar_title.set_symbol_font_size(FONT.TOP_BAR)
        self.bar_title.set_text("Set as Wallpaper")
        self.bar_title.set_disabled(False)
        self.bar_title.bind(on_release=top_bar_callback)


class TopBarExpanded():
    """
    TopBarExpanded is the TopBar of the all screens that:
    - Has a Back button for going back to the previous screen.
    - Has a Screenshot button for going to the StartScreen.
    - Has a Settings button for going to the SettingsScreen.
    - Has an Exit button for exiting the app.
    - Has an Options button for hiding the options.
    """
    def __init__(self,
                 top_left_callback,
                 screenshot_callback,
                 options_callback,
                 settings_callback,
                 exit_callback,
                 ):
        self.top_left_callback = top_left_callback

        self.top_bar_container = TopBarContainer()

        self.top_left_button = TopBarButton(img_path=DM.PATH.BACK_IMG, radius_side="right")
        self.top_left_button.bind(on_release=top_left_callback)

        self.bar_title = TopBarTitle()

        self.screenshot_button = TopBarButton(img_path=DM.PATH.SCREENSHOT_IMG, radius_side="left")
        self.screenshot_button.bind(on_release=screenshot_callback)

        self.settings_button = TopBarButton(img_path=DM.PATH.SETTINGS_IMG, radius_side="none")
        self.settings_button.bind(on_release=settings_callback)

        self.exit_button = TopBarButton(img_path=DM.PATH.EXIT_IMG, radius_side="none")
        self.exit_button.bind(on_release=exit_callback)

        self.options_button = TopBarButton(img_path=DM.PATH.OPTIONS_IMG_BLACK, radius_side="none")
        self.options_button.bind(on_release=options_callback)

        self.top_bar_container.add_widget(self.top_left_button)
        self.top_bar_container.add_widget(self.bar_title)
        self.top_bar_container.add_widget(self.screenshot_button)
        self.top_bar_container.add_widget(self.settings_button)
        self.top_bar_container.add_widget(self.exit_button)
        self.top_bar_container.add_widget(self.options_button)
    
    def make_home_bar(self, top_left_callback):
        """Make the home bar"""
        self.top_left_button.set_image(DM.PATH.SCREENSHOT_IMG)
        self.top_left_button.unbind(on_release=self.top_left_callback)
        self.top_left_button.bind(on_release=top_left_callback)
