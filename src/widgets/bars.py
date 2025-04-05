from kivy.animation import Animation, AnimationTransition
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button

from src.widgets.containers import TopBarContainer
from src.widgets.buttons import TopBarTitle, TopBarButton

from src.settings import FONT, PATH, COL, SIZE, SPACE


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

        self.top_left_button = TopBarButton(img_path=PATH.BACK_IMG, radius_side="right")
        self.top_left_button.bind(on_release=top_left_callback)

        self.bar_title = TopBarTitle(text="")

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG, radius_side="left")
        self.options_button.bind(on_release=options_callback)

        self.top_bar_container.add_widget(self.top_left_button)
        self.top_bar_container.add_widget(self.bar_title)
        self.top_bar_container.add_widget(self.options_button)
    
    def make_home_bar(self, top_left_callback, top_bar_callback):
        """Make the home bar"""
        self.top_left_button.set_image(PATH.EDIT_IMG)
        self.top_left_button.unbind(on_release=self.top_left_callback)
        self.top_left_button.bind(on_release=top_left_callback)
        self.bar_title.set_symbol_font_size(FONT.TOP_BAR_SYMBOL)
        self.bar_title.set_text("+")
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

        self.top_left_button = TopBarButton(img_path=PATH.BACK_IMG, radius_side="right")
        self.top_left_button.bind(on_release=top_left_callback)

        self.bar_title = TopBarTitle()

        self.screenshot_button = TopBarButton(img_path=PATH.SCREENSHOT_IMG, radius_side="left")
        self.screenshot_button.bind(on_release=screenshot_callback)

        self.settings_button = TopBarButton(img_path=PATH.SETTINGS_IMG, radius_side="none")
        self.settings_button.bind(on_release=settings_callback)

        self.exit_button = TopBarButton(img_path=PATH.EXIT_IMG, radius_side="none")
        self.exit_button.bind(on_release=exit_callback)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG_BLACK, radius_side="none")
        self.options_button.bind(on_release=options_callback)

        self.top_bar_container.add_widget(self.top_left_button)
        self.top_bar_container.add_widget(self.bar_title)
        self.top_bar_container.add_widget(self.screenshot_button)
        self.top_bar_container.add_widget(self.settings_button)
        self.top_bar_container.add_widget(self.exit_button)
        self.top_bar_container.add_widget(self.options_button)
    
    def make_home_bar(self, top_left_callback):
        """Make the home bar"""
        self.top_left_button.set_image(PATH.EDIT_IMG)
        self.top_left_button.unbind(on_release=self.top_left_callback)
        self.top_left_button.bind(on_release=top_left_callback)


class BottomBar(Button):
    """
    BottomBar is the bottom navigation button that:
    - Brings the user back to the top of the screen
    - Has a background color
    - Has a symbol
    - Is initially hidden
    - Has an animation
    """
    def __init__(self, text="", **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=SIZE.BOTTOM_BAR_HEIGHT,
            padding=[0, SPACE.SPACE_M, 0, 0],
            pos_hint={"center_x": 0.5, "y": -0.15},  # Just below screen
            text=text,
            font_size=FONT.BOTTOM_BAR,
            bold=True,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            opacity=0,  # Start hidden
            **kwargs
        )
        self.visible = False
        self._show_event = None  # Keep this to track animation state

        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def show(self, *args):
        """
        Mark the bottom bar for showing
        Note: Actual animation is now controlled by the parent screen
        """
        if self.visible or self._show_event:
            return
            
        # Mark as visible - animation will be handled by parent
        self.visible = True
        
        # Notify parent screen to handle synchronized animation
        # This is done by the parent screen checking the visible state
        if hasattr(self, "parent_screen") and self.parent_screen:
            self.parent_screen.check_for_bottom_spacer()
    
    def hide(self, *args):
        """
        Mark the bottom bar for hiding
        Note: Actual animation is now controlled by the parent screen
        """
        if not self.visible and not self._show_event:
            return
        
        # Cancel any pending show event
        if self._show_event:
            Clock.unschedule(self._show_event)
            self._show_event = None
            
        # Mark as not visible - animation will be handled by parent
        self.visible = False
        
        # Notify parent screen to handle synchronized animation
        if hasattr(self, "parent_screen") and self.parent_screen:
            self.parent_screen.check_for_bottom_spacer()
