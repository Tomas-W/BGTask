from kivy.animation import Animation, AnimationTransition
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from src.settings import COL, SIZE, SPACE, FONT, STYLE


class TaskContainer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(SIZE.TASK_ITEM_HEIGHT)


class TimeLabel(Label):
    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint = (1, None)
        self.height = dp(SIZE.TIME_LABEL_HEIGHT)
        self.halign = "left"
        self.font_size = dp(FONT.DEFAULT)
        self.bold = True
        self.color = COL.TEXT
        self.padding = [dp(SPACE.FIELD_PADDING_X), 0, dp(SPACE.FIELD_PADDING_X), 0]
        
        self.bind(size=self.setter("text_size"))


class TaskLabel(Label):
    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint = (1, None)
        self.height = dp(SIZE.MESSAGE_LABEL_HEIGHT)
        self.halign = "left"
        self.valign = "top"
        self.font_size = dp(FONT.DEFAULT)
        self.color = COL.TEXT
        self.padding = [dp(SPACE.FIELD_PADDING_X), dp(0)]
        
        self.bind(size=self.setter("text_size"))


class TaskHeader(Label):
    def __init__(self, text: str,**kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint = (1, None)
        self.height = dp(SIZE.HEADER_HEIGHT)
        self.halign = "left"
        self.font_size = dp(FONT.HEADER)
        self.bold = True
        self.color = COL.HEADER
        self.bind(size=self.setter("text_size"))
        

class TaskBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.spacing = dp(SPACE.SPACE_Y_M)
        self.padding = [0, dp(SPACE.SPACE_Y_M), 0, dp(SPACE.SPACE_Y_M)]
        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(*COL.FIELD_ACTIVE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(STYLE.CORNER_RADIUS)]
            )
            self.bind(pos=self._update, size=self._update)

    def _update(self, instance, value):
        """Update background rectangle on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class TextField(BoxLayout):
    """TextInput with TaskGroup-style background"""
    def __init__(self, hint_text="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(SIZE.BUTTON_HEIGHT * 3)
        self.padding = [0, dp(SPACE.SPACE_Y_M), 0, dp(SPACE.SPACE_Y_M)]
        self.border_width = dp(2)
        self._error_message = "Task message is required!"
        
        with self.canvas.before:
            # Background color
            Color(*COL.FIELD_ACTIVE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size,
                radius=[dp(STYLE.CORNER_RADIUS)]
            )
            
            # Border - always there but with transparent color by default
            self.border_color_instr = Color(*COL.OPAQUE)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], 
                    self.size[0], self.size[1], 
                    dp(STYLE.CORNER_RADIUS)
                ),
                width=self.border_width
            )
            
            # Bind position and size updates
            self.bind(pos=self.update_rects, size=self.update_rects)
        
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
        
        # Bind to text changes to remove error styling when typing starts
        self.text_input.bind(text=self._on_text_change)
        
        self.add_widget(self.text_input)
    
    def _on_text_change(self, instance, value):
        """Remove error border when user starts typing"""
        if value.strip():
            self.border_color_instr.rgba = COL.OPAQUE
            # Reset hint text if it was showing an error
            if self.hint_text == self._error_message:
                self.hint_text = "Enter your task here"
    
    def update_rects(self, instance, value):
        """Update background and border rectangles on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
        # Update border rounded rectangle
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            dp(STYLE.CORNER_RADIUS)
        )
    
    def show_error(self):
        """Show error styling on the field"""
        self.hint_text = self._error_message
        self.border_color_instr.rgba = COL.FIELD_ERROR
    
    # Keep the basic properties
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


class ButtonRow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.spacing = dp(SPACE.SPACE_Y_M)


class CustomButton(Button):
    """Button with state management"""
    # Define state constants
    STATE_ACTIVE = "active"
    STATE_INACTIVE = "inactive" 
    STATE_ERROR = "error"
    
    def __init__(self, width: int, color_state: str, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (width, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.font_size = dp(FONT.BUTTON)
        self.color = COL.WHITE
        self.background_color = COL.OPAQUE
        
        self.radius = [dp(STYLE.CORNER_RADIUS)]
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE
        self.color_error = COL.BUTTON_ERROR
        
        # Set initial state
        self.color_state = color_state
        
        # Create the canvas instructons, but don't set color yet
        with self.canvas.before:
            self.color_instr = Color(1, 1, 1)  # Temporary color
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            self.bind(pos=self._update, size=self._update)
        
        # Apply the initial state
        if self.color_state == self.STATE_ACTIVE:
            self.set_active_state()
        elif self.color_state == self.STATE_INACTIVE:
            self.set_inactive_state()
        elif self.color_state == self.STATE_ERROR:
            self.set_error_state()
        else:
            raise ValueError(f"Invalid state: {self.color_state}")

    def _update(self, instance, value):
        """Update background rectangle on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def set_error_state(self):
        """Set button to error state"""
        self.color_state = self.STATE_ERROR
        self.color_instr.rgba = self.color_error
    
    def set_active_state(self):
        """Set button back to normal state"""
        self.color_state = self.STATE_ACTIVE
        self.color_instr.rgba = self.color_active
    
    def set_inactive_state(self):
        """Set button to inactive state"""
        self.color_state = self.STATE_INACTIVE
        self.color_instr.rgba = self.color_inactive


class ButtonFieldActive(BoxLayout):
    """Button field with state management and optional border"""
    # Define state constants
    STATE_ACTIVE = "active"
    STATE_INACTIVE = "inactive" 
    STATE_ERROR = "error"
    
    def __init__(self, text: str, width: int, color_state="active", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (width, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.padding = [dp(SPACE.FIELD_PADDING_X), dp(SPACE.FIELD_PADDING_Y)]
        
        # Color properties
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE
        self.color_error = COL.BUTTON_ERROR
        
        # Set initial state
        self.border_width = dp(2)
        self.color_state = color_state

        self.text = text

        with self.canvas.before:
            # Background color - will be set based on state
            self.color_instr = Color(1, 1, 1)  # Temporary color
            self.bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size, 
                radius=[dp(STYLE.CORNER_RADIUS)]
            )
            
            # Border - initially transparent
            self.border_color_instr = Color(*COL.OPAQUE)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], 
                    self.size[0], self.size[1], 
                    dp(STYLE.CORNER_RADIUS)
                ),
                width=self.border_width
            )
            
            # Bind position and size updates
            self.bind(pos=self._update, size=self._update)
        
        self.label = ButtonFieldLabel(text=self.text)
        self.add_widget(self.label)
        
        # Apply the initial state
        if self.color_state == self.STATE_ACTIVE:
            self._set_active_state()
        elif self.color_state == self.STATE_INACTIVE:
            self._set_inactive_state()
        elif self.color_state == self.STATE_ERROR:
            self._set_error_state()
        else:
            raise ValueError(f"Invalid state: {self.color_state}")
    
    def _update(self, instance, value):
        """Update the background and border on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
        # Update border rounded rectangle
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            dp(STYLE.CORNER_RADIUS)
        )
    
    def set_text(self, text):
        self.label.text = text
    
    def set_text_color(self, color):
        self.label.color = color

    def _set_error_state(self):
        """Set button to error state"""
        self.color_instr.rgba = self.color_error
        self.set_text_color(COL.ERROR_TEXT)
    
    def _set_active_state(self):
        """Set button to active state"""
        self.color_instr.rgba = self.color_active
        self.set_text_color(COL.TEXT)

    def _set_inactive_state(self):
        """Set button to inactive state"""
        self.color_instr.rgba = self.color_inactive
        self.set_text_color(COL.TEXT)

    def show_border(self, color=None):
        """Show border with optional color"""
        if color:
            self.border_color_instr.rgba = color
        else:
            self.border_color_instr.rgba = COL.WHITE
    
    def hide_border(self):
        """Hide the border"""
        self.border_color_instr.rgba = COL.OPAQUE
        self.set_text_color(COL.TEXT)

    def show_error_border(self):
        """Show error border"""
        self.border_color_instr.rgba = COL.FIELD_ERROR
        self.set_text_color(COL.ERROR_TEXT)


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


class ButtonFieldLabel(Label):
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint = (1, 1)
        self.halign = "center"
        self.valign = "middle"
        self.color = COL.TEXT
        self.font_size = dp(FONT.DEFAULT)

        self.bind(size=self.setter("text_size"))


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
