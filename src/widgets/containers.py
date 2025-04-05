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
            padding=[SPACE.SCREEN_PADDING_X, SPACE.SPACE_XXL, 
                    SPACE.SCREEN_PADDING_X, SPACE.SPACE_XXL],
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


class ScrollContainer(BoxLayout):
    """
    Scroll container is the base for all content that:
    - Contains a MainContainer
    - Sets the background color
    - Handles scrolling
    """
    def __init__(self,
                allow_scroll_y=True,
                allow_scroll_x=True,
                scroll_callback=None,
                **kwargs
        ):
        self.container = MainContainer()
        super().__init__(
            orientation="horizontal",
            **kwargs
        )
        self.main_self = None
        self.scroll_threshold_pixels = 800
        self.scroll_callback = scroll_callback
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
        
        # Bottom bar reference - will be set by HomeScreen
        self.bottom_bar = None
        
        self.scroll_view.bind(scroll_y=self._on_scroll)
    
    def _update_bg(self, instance, value):
        """Update the background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _on_scroll(self, instance, value):
        """Handle scroll events to show/hide bottom bar"""
        if not self.bottom_bar or hasattr(self.main_self, "initial_scroll") and self.main_self.initial_scroll:
            return
        
        scrollable_height = instance.children[0].height
        view_height = instance.height
        max_scroll = scrollable_height - view_height

        pixels_scrolled = (1 - value) * max_scroll
        
        # Logic to determine direction - are we scrolling up or down
        scrolling_down = pixels_scrolled > self.last_pixels_scrolled
        scrolling_up = pixels_scrolled < self.last_pixels_scrolled
        
        # Store the current position for the next comparison
        self.last_pixels_scrolled = pixels_scrolled
        
        # Show bottom bar when scrolled beyond threshold
        if pixels_scrolled > self.scroll_threshold_pixels and not self.bottom_bar.visible:
            # Instead of animating directly, just update the visible flag
            # The animation will be handled by the parent screen
            self.bottom_bar.visible = True
            
            # Call the parent's check method to handle synchronized animation
            if self.scroll_callback:
                self.scroll_callback()

        # Hide bottom bar when scrolled less than threshold
        elif pixels_scrolled <= self.scroll_threshold_pixels and self.bottom_bar.visible:
            # Instead of animating directly, just update the visible flag
            # The animation will be handled by the parent screen
            self.bottom_bar.visible = False
            
            # Call the parent's check method to handle synchronized animation
            if self.scroll_callback:
                self.scroll_callback()
        
        # Don't need special handling for _show_event anymore since we're
        # using synchronized animation

    def scroll_to_top(self, *args):
        """Scroll to the top of the scroll view"""
        self.scroll_view.scroll_y = 1
    
    def connect_bottom_bar(self, bar):
        """
        Connect the bottom bar to this scroll container
        
        This establishes a bidirectional relationship:
        - ScrollContainer knows about the BottomBar for scroll events
        - BottomBar knows about its parent screen for animation
        """
        self.bottom_bar = bar
    
    def scroll_by_distance(self, distance_dp):
        """
        Scroll by a specific distance in dp
        
        Args:
            distance_dp: Distance to scroll in dp, positive to scroll up, negative to scroll down
        """
        # Get total scrollable height
        content_height = self.container.height
        view_height = self.scroll_view.height
        scrollable_height = content_height - view_height
        
        if scrollable_height <= 0:
            return  # Nothing to scroll
        
        # Convert distance to scroll_y change
        # scroll_y ranges from 0 to 1, with 1 being at the top
        scroll_y_change = distance_dp / scrollable_height
        
        # Apply direction - negative distance scrolls down (decreasing scroll_y)
        new_scroll_y = self.scroll_view.scroll_y + scroll_y_change
        
        # Clamp between 0 and 1
        new_scroll_y = max(0.0, min(1.0, new_scroll_y))
        
        # Apply scroll
        self.scroll_view.scroll_y = new_scroll_y


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