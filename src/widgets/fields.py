from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window

from src.widgets.labels import ButtonFieldLabel, SettingsFieldLabel

from src.settings import COL, SIZE, SPACE, FONT, STYLE, TEXT, STATE


class TextField(BoxLayout):
    """
    TextField is the base for all text input fields that:
    - Contains a TextInput
    - Has padding between the text input and the border
    - Has a background color
    - Has a border (default is transparent)
    - Applies visible border on error
    - Has a hint text
    - Has an error message
    - Supports n_lines to determine height and multiline behavior
    - Can be made scrollable by wrapping its input in a ScrollView.
    """
    def __init__(self, hint_text="", n_lines=1, scrollable=False, **kwargs):
        self._is_scrollable = scrollable
        
        # Calculate total height based on number of lines and padding
        font_size = FONT.DEFAULT
        if n_lines == 1:
            font_size = FONT.DEFAULT * 1.2
        total_height = (font_size * n_lines) + (2 * SPACE.SPACE_M)  # Account for top and bottom padding
        
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            height=total_height,
            padding=[0, SPACE.SPACE_M, 0, SPACE.SPACE_M],
            **kwargs
        )
        self.border_width = STYLE.BORDER_WIDTH
        self._hint_text = TEXT.TYPE_HINT
        self._error_message = TEXT.TYPE_ERROR
        self.current_text = ""

        with self.canvas.before:
            Color(*COL.FIELD_INPUT)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size,
                radius=[STYLE.RADIUS_M]
            )
            
            # Border - initially transparent
            self.border_color_instr = Color(*COL.OPAQUE)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], 
                    self.size[0], self.size[1], 
                    STYLE.RADIUS_M
                ),
                width=self.border_width
            )
            
            self.bind(pos=self._update, size=self._update)
        
        # Non-scrollable: TextInput's height is fixed.
        # Scrollable: TextInput's height grows with the content.
        text_input_height = total_height - (2 * SPACE.SPACE_M)
        
        self.text_input = TextInput(
            hint_text=hint_text,
            size_hint_y=None if scrollable else 1,
            height=text_input_height,
            multiline=n_lines > 1,
            font_size=FONT.DEFAULT,
            background_color=COL.OPAQUE,
            foreground_color=COL.TEXT,
            padding=[SPACE.FIELD_PADDING_X, 0],
        )

        if not scrollable:
            self.add_widget(self.text_input)
        
        else:	
            self.text_input.size_hint_y = None
            scroll_view = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                effect_cls="ScrollEffect"
            )

            def update_text_input_height(*args):
                self.text_input.height = max(scroll_view.height, self.text_input.minimum_height)
            
            scroll_view.bind(height=update_text_input_height)
            self.text_input.bind(minimum_height=update_text_input_height)

            def scroll_to_bottom(*args):
                def do_scroll(*args):
                    if self.text_input.focus:
                        scroll_view.scroll_y = 0
                Clock.schedule_once(do_scroll)
            
            # Make view follow cursor when typing
            self.text_input.bind(text=scroll_to_bottom)
            
            scroll_view.add_widget(self.text_input)
            self.add_widget(scroll_view)
        
        self.text_input.bind(text=self._on_text_change)        
    
    def on_mouse_pos(self, *args):
        """Handle mouse enter/leave to control parent scrolling"""
        if not self._is_scrollable:
            return
            
        mouse_pos = Window.mouse_pos
        if self.collide_point(*mouse_pos):
            self._disable_parent_scroll()
        else:
            self._enable_parent_scroll()
    
    def _disable_parent_scroll(self):
        """Walk up the widget tree to find and disable parent ScrollViews"""
        parent = self.parent
        while parent:
            if hasattr(parent, 'do_scroll_y'):
                parent.do_scroll_y = False
                break
            parent = parent.parent
    
    def _enable_parent_scroll(self):
        """Walk up the widget tree to find and re-enable parent ScrollViews"""
        parent = self.parent
        while parent:
            if hasattr(parent, 'do_scroll_y'):
                parent.do_scroll_y = True
                break
            parent = parent.parent

    def _on_text_change(self, instance, value):
        """Remove error border when user starts typing"""
        if value.strip():
            self.set_border_color(COL.OPAQUE)
            self.set_text_color(COL.TEXT)
            # Reset hint text if it was showing an error
            if self.hint_text == self._error_message:
                self.hint_text = self._hint_text
    
    def _update(self, instance, value):
        """Update background and border"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            STYLE.RADIUS_M
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
        self.border_color_instr.rgba = COL.OPAQUE
        self.set_text_color(COL.TEXT)

    def show_error_border(self):
        """Show error styling on the field"""
        self.set_hint_text(self._error_message)
        self.set_text_color(COL.ERROR)
        self.set_border_color(COL.ERROR)
    
    def set_text(self, text):
        self.text_input.text = text
    
    def set_hint_text(self, text):
        self.hint_text = text
    
    def set_text_color(self, color):
        self.text_input.foreground_color = color
    
    def load_text(self):
        self.text_input.text = self.current_text
    
    def save_text(self, text):
        self.current_text = text
    
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


class InputField(BoxLayout):
    """
    InputField is the base for all text input fields that:
    - Contains a TextInput
    - Has padding between the text input and the border
    - Has a background color
    - Has a border (default is transparent)
    - Applies visible border on error
    - Has a hint text
    - Has an error message
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(0.5, 1),
            pos_hint={"center_y": 0.5},
            **kwargs
        )
        self.border_width = STYLE.BORDER_WIDTH
        self.current_text = ""

        with self.canvas.before:
            Color(*COL.FIELD_INPUT)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size,
                radius=[STYLE.RADIUS_S]
            )
            
            # Border - initially transparent
            self.border_color_instr = Color(*COL.OPAQUE)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], 
                    self.size[0], self.size[1], 
                    STYLE.RADIUS_S
                ),
                width=self.border_width
            )
            
            self.bind(pos=self._update, size=self._update)
        
        self.text_input = TextInput(
            size_hint=(1, 1),
            multiline=False,
            font_size=FONT.HEADER,
            background_color=COL.OPAQUE,
            foreground_color=COL.TEXT,
            padding=[FONT.HEADER/3],
            halign="center",
        )
        
        self.text_input.bind(text=self._on_text_change)        
        self.add_widget(self.text_input)
    
    def _on_text_change(self, instance, value):
        """Remove error border when user starts typing"""
        if value.strip():
            self.set_border_color(COL.OPAQUE)
            self.set_text_color(COL.TEXT)

    def _update(self, instance, value):
        """Update background and border"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            STYLE.RADIUS_M
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
        self.border_color_instr.rgba = COL.OPAQUE
        self.set_text_color(COL.TEXT)

    def show_error_border(self):
        """Show error styling on the field"""
        self.set_text_color(COL.ERROR)
        self.set_border_color(COL.ERROR)
    
    def set_text(self, text):
        self.text_input.text = text
    
    def set_hint_text(self, text):
        self.hint_text = text
    
    def set_text_color(self, color):
        self.text_input.foreground_color = color
    
    def load_text(self):
        self.text_input.text = self.current_text
    
    def save_text(self, text):
        self.current_text = text
    
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
    """
    ButtonField is a text only field that looks like a CustomButton that:
    - Has a state (active, inactive, error)
    - Has a Label for text
    - Has a background color based on state
    - Has a border (default is transparent)
    - Applies visible border on error
    """
    def __init__(self, text: str, width: int, color_state=STATE.ACTIVE, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(width, None),
            height=SIZE.BUTTON_HEIGHT,
            padding=[SPACE.FIELD_PADDING_X, SPACE.FIELD_PADDING_Y],
            **kwargs
        )
        
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE
        self.color_error = COL.ERROR
        
        self.border_width = STYLE.BORDER_WIDTH
        self.color_state = color_state
        self.text = text

        with self.canvas.before:
            # Background color - will be set based on state
            self.color_instr = Color(1, 1, 1)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size, 
                radius=[STYLE.RADIUS_M]
            )
            
            # Border - initially transparent
            self.border_color_instr = Color(*COL.OPAQUE)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], 
                    self.size[0], self.size[1], 
                    STYLE.RADIUS_M
                ),
                width=self.border_width
            )
            
            self.bind(pos=self._update, size=self._update)
        
        self.label = ButtonFieldLabel(text=self.text)
        self.label.color = COL.TEXT
        self.add_widget(self.label)
        
        # Apply the initial state
        if self.color_state == STATE.ACTIVE:
            self._set_active_state()
        elif self.color_state == STATE.INACTIVE:
            self._set_inactive_state()
        elif self.color_state == STATE.ERROR:
            self._set_error_state()
        else:
            raise ValueError(f"Invalid state: {self.color_state}")
    
    def _update(self, instance, value):
        """Update the background and border"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            STYLE.RADIUS_M
        )
    
    def set_text(self, text):
        self.label.text = text

    def _set_error_state(self):
        self.color_instr.rgba = self.color_error
    
    def _set_active_state(self):
        self.color_instr.rgba = self.color_active

    def _set_inactive_state(self):
        self.color_instr.rgba = self.color_inactive

    def show_border(self, color=None):
        """Show border with optional color"""
        if color:
            self.border_color_instr.rgba = color
    
    def hide_border(self):
        self.border_color_instr.rgba = COL.OPAQUE

    def show_error_border(self):
        self.border_color_instr.rgba = COL.ERROR


class SettingsField(ButtonField):
    """
    SettingsField is a text only field that looks like a CustomButton that:
    - Has a state (active, inactive, error)
    - Has a Label for text
    - Has a background color based on state
    - Has a border (default is transparent)
    - Is half the height of the CustomButton
    """
    def __init__(self, text: str, width: int, color_state=STATE.ACTIVE, **kwargs):
        super().__init__(
            text=text,
            width=width,
            color_state=color_state,
            **kwargs
        )
        self.height = SIZE.SETTINGS_BUTTON_HEIGHT
        self.font_size = FONT.SETTINGS_BUTTON
        self.remove_widget(self.label)
        self.label = SettingsFieldLabel(text=self.text)
        self.add_widget(self.label)


class CustomSettingsField(ButtonField):
    """
    CustomSettingsField is a text only field that looks like a CustomButton that:
    - Has a state (active, inactive, error)
    - Has a Label for text
    - Has a background color based on state
    - Has a border (default is transparent)
    - Is 2/3 the height of the CustomButton
    - Can have top or bottom corners made sharp
    """
    def __init__(self, text: str, width: int, color_state=STATE.ACTIVE, **kwargs):
        super().__init__(
            text=text,
            width=width,
            color_state=color_state,
            **kwargs
        )
        self.height = SIZE.SETTINGS_BUTTON_HEIGHT
        self.font_size = FONT.SETTINGS_BUTTON
        self.remove_widget(self.label)
        self.label = SettingsFieldLabel(text=self.text)
        self.add_widget(self.label)
        
        self._default_radius = STYLE.RADIUS_M
        self._current_radius = [self._default_radius] * 4
    
    def remove_top_radius(self):
        """Remove the top rounded corners, making them sharp"""
        self._current_radius[0] = 0
        self._current_radius[1] = 0
        self._update_radius()
    
    def remove_bottom_radius(self):
        """Remove the bottom rounded corners, making them sharp"""
        self._current_radius[2] = 0
        self._current_radius[3] = 0
        self._update_radius()
    
    def reset_radius(self):
        """Reset all corners to default rounded state"""
        self._current_radius = [self._default_radius] * 4
        self._update_radius()
    
    def _update_radius(self):
        """Update both background and border radius"""
        self.bg_rect.radius = self._current_radius
        self.border_rect.rounded_rectangle = (
            self.pos[0], self.pos[1],
            self.size[0], self.size[1],
            self._current_radius[0]
        )
    
    def set_active(self):
        self.color_instr.rgba = COL.CONFIRM_BUTTON_INACTIVE

    def set_inactive(self):
        self.color_instr.rgba = COL.BUTTON_INACTIVE