from kivy.animation import Animation, AnimationTransition
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from src.settings import COL, SIZE, SPACE


class MainContainer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SPACE.SPACE_Y_XL),
            padding=[dp(SPACE.SCREEN_PADDING_X), dp(30), 
                    dp(SPACE.SCREEN_PADDING_X), dp(50)],
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))
        
        with self.canvas.before:
            Color(*COL.BG_WHITE)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class ScrollContainer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        
        # Container for content
        self.container = MainContainer()
        
        # Scrolling
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True
        )
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)
        
        # Bottom bar reference - will be set by HomeScreen
        self.bottom_bar = None
        self.scroll_threshold = 0.8  # Value to trigger bottom bar
        
        # Bind scroll event
        self.scroll_view.bind(scroll_y=self._on_scroll)
    
    def _on_scroll(self, instance, value):
        """Handle scroll events to show/hide bottom bar"""
        if not self.bottom_bar:
            return
            
        # Show bottom bar when scrolled down
        if value < self.scroll_threshold and not self.bottom_bar.visible:
            self.bottom_bar.show()
        # Hide bottom bar when at/near the top
        elif value >= self.scroll_threshold and self.bottom_bar.visible:
            self.bottom_bar.hide()
    
    def scroll_to_top(self):
        """Scroll to the top of the scroll view"""
        self.scroll_view.scroll_y = 1
    
    def set_bottom_bar(self, bar):
        """Connect the bottom bar to this scroll container"""
        self.bottom_bar = bar
    
    def clear_widgets(self):
        """Clear the container widgets"""
        self.container.clear_widgets()
    
    def add_widget_to_container(self, widget):
        """Add widget to the container"""
        self.container.add_widget(widget)


class TopBar(Button):
    def __init__(self, text="", **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=dp(SIZE.TOP_BAR_HEIGHT),
            text=text,
            font_size=dp(SIZE.TOP_BAR_FONT),
            bold=True,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class BottomBar(Button):
    def __init__(self, text="", **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=dp(SIZE.BOTTOM_BAR_HEIGHT),
            padding=[0, dp(SPACE.SPACE_Y_M), 0, 0],
            pos_hint={"center_x": 0.5, "y": -0.15},  # Just below screen
            text=text,
            font_size=dp(SIZE.TOP_BAR_FONT),
            bold=True,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            opacity=0,  # Start hidden
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
        
        self.visible = False
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def show(self):
        """Animate the bottom bar into view with smooth sliding"""
        if self.visible:
            return
            
        self.visible = True
        
        # Slide up and fade in
        anim = Animation(
            opacity=1, 
            pos_hint={"center_x": 0.5, "y": 0}, 
            duration=0.3,
            transition=AnimationTransition.out_quad
        )
        anim.start(self)
    
    def hide(self):
        """Animate the bottom bar out of view with smooth sliding"""
        if not self.visible:
            return
            
        self.visible = False
        
        # Slide down and fade out
        anim = Animation(
            opacity=0, 
            pos_hint={"center_x": 0.5, "y": -0.15}, 
            duration=0.3,
            transition=AnimationTransition.in_quad
        )
        anim.start(self)


class Spacer(BoxLayout):
    def __init__(self, height=SPACE.SPACE_Y_XL, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(height),
            **kwargs
        )
