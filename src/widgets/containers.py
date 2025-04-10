from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from kivy.logger import Logger as logger

from src.settings import COL, SIZE, SPACE, FONT


class BaseLayout(BoxLayout):
    """
    Base layout for all screens that:
    - Contains a TopBar, ScrollContainer and a BottomBar
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"top": 1, "center_x": 0.5},
            **kwargs
        )


class MainContainer(BoxLayout):
    """
    Main container is the base for the ScrollContainer that:
    - Sets spacing between its children
    - Sets padding between the screen edges and itself
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=SPACE.SPACE_XL,
            padding=[SPACE.SCREEN_PADDING_X, SPACE.SPACE_XXL],
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))
        
        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class StartContainer(BoxLayout):
    """
    Start container is the base for the StartScreen that:
    - Contains a MainContainer
    - Has a background color
    - Sets spacing between its children

    """
    def __init__(self, parent_screen, **kwargs):
        self.container = MainContainer()
        self.container.spacing = SPACE.SPACE_MAX
        super().__init__(
            orientation="vertical",
            **kwargs
        )
        self.parent_screen = parent_screen

        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg, size=self._update_bg)

        self.scroll_view = ScrollView(
            do_scroll_x=True,
            do_scroll_y=True,
            scroll_wheel_distance=60,
        )
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)
        
    def _update_bg(self, instance, value):
        """Update the background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def on_touch_down(self, touch):
        # Store the initial touch position
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        # Calculate the distance moved
        delta_x = touch.x - self.touch_start_x
        delta_y = touch.y - self.touch_start_y
        
        # Determine if the swipe is significant enough
        if abs(delta_x) > 10 or abs(delta_y) > 10:  # Adjust threshold as needed
            if abs(delta_x) > abs(delta_y):  # Horizontal swipe
                if delta_x > 0:
                    self.on_swipe_right()
                else:
                    self.on_swipe_left()
            else:  # Vertical swipe
                if delta_y > 0:
                    self.on_swipe_up()
                else:
                    self.on_swipe_down()
        
        return super().on_touch_up(touch)
    
    def on_swipe_right(self):
        if self.parent_screen:
            self.parent_screen.navigate_to_home_screen("right")
    
    def on_swipe_left(self):
        if self.parent_screen:
            self.parent_screen.navigate_to_home_screen("left")
    
    def on_swipe_up(self):
        pass
    
    def on_swipe_down(self):
        pass


class ScrollContainer(BoxLayout):
    """
    Scroll container is the base for all content that:
    - Contains a MainContainer
    - Sets the background color
    - Handles scrolling
    """
    def __init__(self,
                parent_screen,
                scroll_callback,
                allow_scroll_y,
                allow_scroll_x,
                **kwargs
        ):
        self.container = MainContainer()
        super().__init__(
            orientation="horizontal",
            **kwargs
        )
        self.parent_screen = parent_screen
        self.scroll_callback = scroll_callback

        self.scroll_threshold_pixels = 800
        self.last_pixels_scrolled = 0  # Track the last scroll position
        
        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg, size=self._update_bg)

        self.scroll_view = ScrollView(
            do_scroll_x=allow_scroll_x,
            do_scroll_y=allow_scroll_y,
            scroll_wheel_distance=80,
        )
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)
        
        self.scroll_view.bind(scroll_y=self._on_scroll)
    
    def _update_bg(self, instance, value):
        """Update the background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _on_scroll(self, instance, value):
        """Handle scroll events to show/hide bottom bar"""
        if not self.parent_screen.bottom_bar:
            return
        
        if self.parent_screen.initial_scroll:
            return
        
        scrollable_height = instance.children[0].height
        view_height = instance.height
        max_scroll = scrollable_height - view_height

        pixels_scrolled = (1 - value) * max_scroll

        # Store the current position for the next comparison
        self.last_pixels_scrolled = pixels_scrolled
        
        # Skip visibility changes during active touch events to prevent scroll jumping
        if self.scroll_view._touch is not None:
            return
        
        # Show bottom bar when scrolled beyond threshold
        if pixels_scrolled > self.scroll_threshold_pixels and not self.parent_screen.bottom_bar.visible:
            # Instead of animating directly, just update the visible flag
            # The animation will be handled by the parent screen
            self.parent_screen.bottom_bar.visible = True
            
            # Call the parent's check method to handle synchronized animation
            if self.scroll_callback:
                self.scroll_callback()

        # Hide bottom bar when scrolled less than threshold
        elif pixels_scrolled <= self.scroll_threshold_pixels and self.parent_screen.bottom_bar.visible:
            # Instead of animating directly, just update the visible flag
            # The animation will be handled by the parent screen
            self.parent_screen.bottom_bar.visible = False
            
            # Call the parent's check method to handle synchronized animation
            if self.scroll_callback:
                self.scroll_callback()

    def scroll_to_top(self, *args):
        """Scroll to the top of the scroll view"""
        # Stop any ongoing scrolling by resetting the scroll effect
        if hasattr(self.scroll_view, "effect_y"):
            self.scroll_view.effect_y.value = 0
            self.scroll_view.effect_y.velocity = 0
        
        # Clear any active touch that might be causing scrolling
        self.scroll_view._touch = None
        
        # Force scroll position to top
        self.scroll_view.scroll_y = 1


class TopBarContainer(BoxLayout):
    """
    Top bar container is the base for the TopBar that:
    - Sets a background color
    """
    def __init__(self, **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=SIZE.TOP_BAR_HEIGHT,
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class Partition(BoxLayout):
    """
    Partition is the base for all content with similar functionality that:
    - Sets spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            spacing=SPACE.SPACE_S,
            **kwargs
        )
        self.bind(minimum_height=self.setter('height'))


class CustomButtonRow(BoxLayout):
    """
    CustomButtonRow is the base for a row of CustomButtons that:
    - Contains CustomButtons
    - Has spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            height=SIZE.BUTTON_HEIGHT,
            spacing=SPACE.SPACE_M,
            **kwargs
        )


class CustomSettingsButtonsRow(CustomButtonRow):
    """
    CustomSettingsButtonsRow is the base for a row of CustomSettingsButtons that:
    - Contains CustomSettingsButtons
    - Has spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs
        )
        self.height = SIZE.SETTINGS_BUTTON_HEIGHT

class CustomRow(BoxLayout):
    """
    CustomRow is the base for a row of widgets that:
    - Contains widgets
    - Has spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(0.5, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            height=2 * FONT.HEADER,
            spacing=SPACE.SPACE_XS,
            **kwargs
        )
    #     with self.canvas.before:
    #         Color(*COL.RED)
    #         self.bg_rect = Rectangle(pos=self.pos, size=self.size)
    #         self.bind(pos=self._update, size=self._update)
    
    # def _update(self, instance, value):
    #     self.bg_rect.pos = instance.pos
    #     self.bg_rect.size = instance.size