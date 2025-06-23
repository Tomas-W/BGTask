from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from src.settings import COL, FONT, SIZE, SPACE, STYLE


class CalendarContainer(BoxLayout):
    """Container for the calendar"""
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            height=SIZE.CALENDAR_HEIGHT,
            spacing=SPACE.SPACE_S,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class CalendarHeadersContainer(GridLayout):
    """GridLayout for the calendar headers"""
    def __init__(self, **kwargs):
        super().__init__(
            cols=7,
            size_hint=(1, None),
            height=SIZE.HEADER_HEIGHT,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class CalendarHeaderLabel(Label):
    """Label for the calendar header"""
    def __init__(self, text, **kwargs):
        super().__init__(
            text=text,
            bold=True,
            color=COL.TEXT,
            font_size=FONT.DEFAULT,
            size_hint_y=None,
            height=FONT.DEFAULT,
            **kwargs
        )
        self.bind(height=self.setter("height"))


class CalendarGrid(GridLayout):
    """GridLayout for the calendar"""
    def __init__(self, **kwargs):
        super().__init__(
            cols=7,
            size_hint=(1, None),
            height=7 * SIZE.HEADER_HEIGHT,  # Max 6 weeks, + 1 for spacing below
            **kwargs
        )
        self.bind(height=self.setter("height"))


class DateTimeLabel(ButtonBehavior, Label):
    """A clickable date/time label with visual states for current day and selected day"""
    
    def __init__(self, **kwargs):
        super().__init__(
            font_size=FONT.DEFAULT,
            color=COL.TEXT_GREY,
            bold=True,
            size_hint_y=None,
            height=SIZE.DATE_TIME_LABEL,
            halign="center",
            valign="center",
            **kwargs
        )
        
        self._is_current_day = False
        self._is_selected = False
        
        self._background = None
        self._border = None
        self._border_inner = None
        self._border_width = dp(2)
        
        # Setup bindings
        self.bind(size=self._update_text_size)
        self._update_text_size()

    def _update_text_size(self, *args):
        """Ensure text is properly centered within the widget"""
        self.text_size = self.size

    def set_bold(self, is_bold: bool):
        """Update text style based on selection state"""
        self.font_size = FONT.DEFAULT_BOLD if is_bold else FONT.DEFAULT
        self.color = COL.BLACK if is_bold else COL.TEXT_GREY

    def update_style(self):
        """Update all visual elements based on current state"""
        self.canvas.before.clear()
        
        with self.canvas.before:
            if self._is_selected:
                # Outer rect
                Color(*COL.BUTTON_ACTIVE)
                self._border = RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=[STYLE.RADIUS_S]
                )
                
                # Inner rect
                Color(*COL.BG)
                self._border_inner = RoundedRectangle(
                    pos=(self.pos[0] + self._border_width, self.pos[1] + self._border_width),
                    size=(self.size[0] - (2 * self._border_width), self.size[1] - (2 * self._border_width)),
                    radius=[STYLE.RADIUS_S]
                )
            
            if self._is_current_day:
                Color(*COL.FIELD_INPUT)
                self._background = RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=[STYLE.RADIUS_S]
                )

        # Update text style
        self.color = COL.TEXT_GREY
        self.set_bold(self._is_selected)
        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def set_current_day(self, is_current: bool):
        """Set the current day highlight state"""
        self._is_current_day = is_current
        self.update_style()

    def set_selected(self, is_selected: bool):
        """Set the selected state"""
        self._is_selected = is_selected
        self.update_style()

    def _update_graphics(self, *args):
        """Update positions and sizes of all graphics elements"""
        if self._is_selected and self._border and self._border_inner:
            self._border.pos = self.pos
            self._border.size = self.size
            self._border_inner.pos = (self.pos[0] + self._border_width, self.pos[1] + self._border_width)
            self._border_inner.size = (self.size[0] - (2 * self._border_width), self.size[1] - (2 * self._border_width))
        
        if self._is_current_day and self._background:
            self._background.pos = self.pos
            self._background.size = self.size


class TimeInputField(BoxLayout):
    """
    A specialized time input field with separate hours and minutes inputs and a colon separator.
    Features a unified appearance with a single background and border.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(0.45, None),
            height=SIZE.HEADER_HEIGHT * 2,
            **kwargs
        )
        
        self.border_width = STYLE.BORDER_WIDTH
        
        # Background and border
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
        
        # Hours input
        self.hours_input = TextInput(
            size_hint=(0.2, 1),
            multiline=False,
            font_size=FONT.HEADER,
            background_color=COL.OPAQUE,
            foreground_color=COL.TEXT,
            padding=[FONT.HEADER/3],
            halign="right",
            input_filter="int",
            write_tab=False,
        )
        self.hours_input.bind(text=self._limit_hours_input)
        
        # Colon separator
        self.colon_label = Label(
            text=":",
            size_hint_x=0.05,
            font_size=FONT.HEADER,
            color=COL.TEXT,
            bold=True
        )
        
        # Minutes input
        self.minutes_input = TextInput(
            size_hint=(0.2, 1),
            multiline=False,
            font_size=FONT.HEADER,
            background_color=COL.OPAQUE,
            foreground_color=COL.TEXT,
            padding=[FONT.HEADER/3],
            halign="left",
            input_filter="int",
            write_tab=False,
        )
        self.minutes_input.bind(text=self._limit_minutes_input)
        
        self.add_widget(self.hours_input)
        self.add_widget(self.colon_label)
        self.add_widget(self.minutes_input)

    def _on_width(self, instance, value):
        """Adjust parent's width when TimeInputField is added to it"""
        if value:
            value.width = self.width

    def _limit_hours_input(self, instance, value):
        """Limit hours input to 2 digits"""
        if len(value) > 2:
            instance.text = value[:2]
    
    def _limit_minutes_input(self, instance, value):
        """Limit minutes input to 2 digits"""
        if len(value) > 2:
            instance.text = value[:2]

    def _update(self, instance, value):
        """Update background and border"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            STYLE.RADIUS_S
        )
    
    def set_border_color(self, color):
        """Set border color"""
        self.border_color_instr.rgba = color

    def show_error_border(self):
        """Show error styling on the field"""
        self.set_text_color(COL.ERROR)
        self.set_border_color(COL.ERROR)

    def hide_border(self):
        """Hide the border"""
        self.border_color_instr.rgba = COL.OPAQUE
        self.set_text_color(COL.TEXT)

    def set_text(self, text):
        """Set text with proper formatting"""
        if not text:
            self.hours_input.text = ""
            self.minutes_input.text = ""
            return
            
        # Handle datetime.time objects
        if hasattr(text, "hour") and hasattr(text, "minute"):
            self.hours_input.text = f"{text.hour:02d}"
            self.minutes_input.text = f"{text.minute:02d}"
        elif isinstance(text, str):
            # Parse string format
            parts = text.split(":")
            if len(parts) == 2:
                hours = parts[0].strip()
                minutes = parts[1].strip()
                self.hours_input.text = hours
                self.minutes_input.text = minutes

    def set_text_color(self, color):
        """Set text color for both inputs"""
        self.hours_input.foreground_color = color
        self.minutes_input.foreground_color = color
        self.colon_label.color = color

    def get_time(self):
        """Get the current time as a tuple of (hours, minutes)"""
        try:
            hours_str = self.hours_input.text.strip()
            minutes_str = self.minutes_input.text.strip()
            
            if not hours_str or not minutes_str:
                return None
                
            hours = int(hours_str)
            minutes = int(minutes_str)
            
            # Validate hours and minutes
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                return (hours, minutes)
                
        except (ValueError, AttributeError):
            pass
        
        return None

    @property
    def text(self):
        """Get combined hours:minutes text"""
        hours = self.hours_input.text.strip()
        minutes = self.minutes_input.text.strip()
        
        if not hours and not minutes:
            return ""
            
        return f"{hours}:{minutes}"
