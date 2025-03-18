from kivy.animation import Animation, AnimationTransition
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from src.settings import COL, SIZE, SPACE, FONT, STYLE


class StyledTextInput(BoxLayout):
    """TextInput with TaskGroup-style background"""
    def __init__(self, hint_text="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(SIZE.BUTTON_HEIGHT * 3)
        self.padding = [0, dp(SPACE.SPACE_Y_M), 0, dp(SPACE.SPACE_Y_M)]
        
        with self.canvas.before:
            Color(*COL.FIELD_BG)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size,
                radius=[dp(STYLE.CORNER_RADIUS)]
            )
            self.bind(pos=self.update_bg_rect, size=self.update_bg_rect)
        
        self.text_input = TextInput(
            hint_text=hint_text,
            size_hint=(1, None),
            height=dp(SIZE.BUTTON_HEIGHT * 3) - dp(SPACE.SPACE_Y_M) * 2,
            multiline=True,
            font_size=dp(FONT.DEFAULT),
            background_color=COL.OPAQUE,
            foreground_color=COL.TEXT,
            padding=[dp(SPACE.FIELD_PADDING_X), 0]
        )
        
        self.add_widget(self.text_input)
    
    def update_bg_rect(self, instance, value):
        """Update background rectangle on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
    @property
    def text(self):
        return self.text_input.text
        
    @text.setter
    def text(self, value):
        self.text_input.text = value
        
    @property
    def hint_text(self):
        return self.text_input.hint_text
        
    @hint_text.setter
    def hint_text(self, value):
        self.text_input.hint_text = value
        
    @property
    def background_color(self):
        return self.text_input.background_color
        
    @background_color.setter
    def background_color(self, value):
        self.text_input.background_color = value


class ButtonActive(Button):
    """Full width active button"""
    def __init__(self, width: int, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (width, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.font_size = dp(FONT.BUTTON)
        self.color = COL.WHITE
        self.background_color = COL.OPAQUE
        
        self.radius = [dp(STYLE.CORNER_RADIUS)]
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE

        with self.canvas.before:
            Color(*self.color_active)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            self.bind(pos=self._update, size=self._update)

    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class ButtonInactive(Button):
    """Full width inactive button"""
    def __init__(self, width: int, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (width, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.font_size = dp(FONT.BUTTON)
        self.color = COL.WHITE
        self.background_color = COL.OPAQUE
        
        self.radius = [dp(STYLE.CORNER_RADIUS)]
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE

        with self.canvas.before:
            Color(*self.color_inactive)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(STYLE.CORNER_RADIUS)])
            self.bind(pos=self._update, size=self._update)
        
    def _update(self, instance, value):
        """Update the date display background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class ButtonFieldActive(BoxLayout):
    """Button field active"""
    def __init__(self, width: int, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (width, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.padding = [dp(SPACE.FIELD_PADDING_X), dp(SPACE.FIELD_PADDING_Y)]

        with self.canvas.before:
            Color(*COL.BUTTON_ACTIVE)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(STYLE.CORNER_RADIUS)])
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        """Update the date display background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class ButtonFieldInactive(BoxLayout):
    """Button field inactive"""
    def __init__(self, width: int, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (width, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.padding = [dp(SPACE.FIELD_PADDING_X), dp(SPACE.FIELD_PADDING_Y)]

        with self.canvas.before:
            Color(*COL.BUTTON_INACTIVE)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(STYLE.CORNER_RADIUS)])
            self.bind(pos=self._update, size=self._update)
        
    def _update(self, instance, value):
        """Update the date display background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size



class MainContainer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SPACE.SPACE_Y_XL),
            padding=[dp(SPACE.SCREEN_PADDING_X), dp(SPACE.SPACE_Y_XL), 
                    dp(SPACE.SCREEN_PADDING_X), dp(SPACE.SPACE_Y_XXL)],
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
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        
        # Set background for entire scroll area
        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg, size=self._update_bg)
        
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
            
        if value < self.scroll_threshold and not self.bottom_bar.visible:
            self.bottom_bar.show()
        elif value >= self.scroll_threshold and self.bottom_bar.visible:
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


class TopBar(Button):
    def __init__(self, text="", button=True,**kwargs):
        super().__init__(
            size_hint=(1, None),
            height=dp(SIZE.TOP_BAR_HEIGHT),
            text=text,
            font_size=dp(FONT.TOP_BAR_SYMBOL) if button else dp(FONT.TOP_BAR),
            bold=True,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BUTTON_ACTIVE)
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
            font_size=dp(FONT.BOTTOM_BAR),
            bold=True,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            opacity=0,  # Start hidden
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BUTTON_ACTIVE)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
        
        self.visible = False
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def show(self, *args):
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
    
    def hide(self, *args):
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
