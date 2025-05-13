from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

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
                Color(*COL.FIELD_ACTIVE)
                self._background = RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=[STYLE.RADIUS_S]
                )

        # Update text appearance
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
