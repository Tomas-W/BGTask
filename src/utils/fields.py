from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

from src.utils.labels import ButtonFieldLabel

from src.settings import COL, SIZE, SPACE, FONT, STYLE, TEXT


class TextField(BoxLayout):
    """TextInput with TaskGroup-style background"""
    def __init__(self, hint_text="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(SIZE.BUTTON_HEIGHT * 3)
        self.padding = [0, dp(SPACE.SPACE_Y_M), 0, dp(SPACE.SPACE_Y_M)]
        self.border_width = dp(2)
        self._hint_text = TEXT.TYPE_HINT
        self._error_message = TEXT.TYPE_ERROR
        self.current_text = ""

        with self.canvas.before:
            # Background color
            Color(*COL.FIELD_ACTIVE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size,
                radius=[dp(STYLE.RADIUS_L)]
            )
            
            # Border - always there but with transparent color by default
            self.border_color_instr = Color(*COL.OPAQUE)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], 
                    self.size[0], self.size[1], 
                    dp(STYLE.RADIUS_L)
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
            self.set_border_color(COL.OPAQUE)
            self.set_text_color(COL.TEXT)
            # Reset hint text if it was showing an error
            if self.hint_text == self._error_message:
                self.hint_text = self._hint_text
    
    def update_rects(self, instance, value):
        """Update background and border rectangles on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
        # Update border rounded rectangle
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            dp(STYLE.RADIUS_L)
        )
    
    def set_border_color(self, color):
        self.border_color_instr.rgba = color

    def show_border(self, color=None):
        """Show border with optional color"""
        if color:
            self.set_border_color(color)
        else:
            self.set_border_color(COL.WHITE)
    
    def hide_border(self):
        """Hide the border"""
        self.border_color_instr.rgba = COL.OPAQUE
        self.set_text_color(COL.TEXT)

    def show_error_border(self):
        """Show error styling on the field"""
        self.set_hint_text(self._error_message)
        self.set_text_color(COL.ERROR_TEXT)
        self.set_border_color(COL.FIELD_ERROR)
    
    def set_hint_text(self, text):
        self.hint_text = text
    
    def set_text_color(self, color):
        self.text_input.foreground_color = color
    
    def load_text(self):
        self.text_input.text = self.current_text
    
    def save_text(self, text):
        self.current_text = text
    
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



class ButtonField(BoxLayout):
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
                radius=[dp(STYLE.RADIUS_L)]
            )
            
            # Border - initially transparent
            self.border_color_instr = Color(*COL.OPAQUE)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], 
                    self.size[0], self.size[1], 
                    dp(STYLE.RADIUS_L)
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
            dp(STYLE.RADIUS_L)
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
