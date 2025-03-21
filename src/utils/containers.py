from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from kivy.uix.scrollview import ScrollView

from src.settings import COL, SIZE, SPACE, STYLE


class TopBarContainer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=dp(SIZE.TOP_BAR_HEIGHT),
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class BaseLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"top": 1, "center_x": 0.5},
            **kwargs
        )


class MainContainer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SPACE.SPACE_XL),
            padding=[dp(SPACE.SCREEN_PADDING_X), dp(SPACE.SPACE_XXL), 
                    dp(SPACE.SCREEN_PADDING_X), dp(SPACE.SPACE_XXL)],
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
    def __init__(self,
                allow_scroll_y=True,
                allow_scroll_x=False,
                **kwargs
        ):
        # Container for content
        self.container = MainContainer()
        super().__init__(
            orientation="vertical",
            **kwargs
        )
        self.scroll_threshold_pixels = 200
        
        # Set background for entire scroll area
        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg, size=self._update_bg)
        
        
        
        # Scrolling
        self.scroll_view = ScrollView(
            do_scroll_x=allow_scroll_x,
            do_scroll_y=allow_scroll_y
        )
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)
        
        # Bottom bar reference - will be set by HomeScreen
        self.bottom_bar = None
        self.scroll_threshold = 0.8
        
        self.scroll_view.bind(scroll_y=self._on_scroll)
    
    def _update_bg(self, instance, value):
        """Update the background rectangle"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _on_scroll(self, instance, value):
        """Handle scroll events to show/hide bottom bar"""
        if not self.bottom_bar:
            return
        scrollable_height = instance.children[0].height  # Total height of the scrollable content
        view_height = instance.height  # Height of the visible viewport
        max_scroll = scrollable_height - view_height  # Maximum scrollable distance

        # Calculate pixels scrolled from the top
        pixels_scrolled = (1 - value) * max_scroll  # Since scroll_y = 1 at the top

        if pixels_scrolled > self.scroll_threshold_pixels and not self.bottom_bar.visible:
            self.bottom_bar.show()
        elif pixels_scrolled <= self.scroll_threshold_pixels and self.bottom_bar.visible:
            self.bottom_bar.hide()
    
    def scroll_to_top(self, *args):
        """Scroll to the top of the scroll view
        
        The *args parameter allows this method to be used as an event handler
        for button presses, which pass the button instance as an argument.
        """
        self.scroll_view.scroll_y = 1
    
    def connect_bottom_bar(self, bar):
        """Connect the bottom bar to this scroll container"""
        self.bottom_bar = bar
    
    def clear_widgets(self):
        """Clear the container widgets"""
        self.container.clear_widgets()
    
    def add_widget_to_container(self, widget):
        """Add widget to the container"""
        self.container.add_widget(widget)


class Partition(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)  # Allow variable height
        self.spacing = dp(SPACE.SPACE_M)

        # Bind the height to the minimum height of the children
        self.bind(minimum_height=self.setter('height'))

    def add_widget(self, widget):
        """Override add_widget to automatically adjust height when a widget is added."""
        super().add_widget(widget)
        # Optionally, you can bind the height of the widget if needed
        widget.bind(size=self._update_height)

    def _update_height(self, instance, value):
        """Update the height of the partition based on its children's heights."""
        self.height = self.minimum_height  # Automatically adjust to fit children


class TaskContainer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(SIZE.TASK_ITEM_HEIGHT)


class TaskBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.spacing = dp(SPACE.SPACE_M)
        self.padding = [0, dp(SPACE.SPACE_M), 0, dp(SPACE.SPACE_M)]
        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(*COL.FIELD_ACTIVE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(STYLE.RADIUS_M)]
            )
            self.bind(pos=self._update, size=self._update)

    def _update(self, instance, value):
        """Update background rectangle on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class ButtonRow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.spacing = dp(SPACE.SPACE_M)
