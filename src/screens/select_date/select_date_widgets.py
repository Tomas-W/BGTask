from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from src.settings import COL, FONT, SIZE, SPACE


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
    """Label that behaves like a button"""
    def __init__(self, **kwargs):
        super().__init__(
            font_size=FONT.DEFAULT,
            color=COL.TEXT_GREY,
            bold=True,
            size_hint_y=None,
            height=SIZE.DATE_TIME_LABEL,
            halign="center",
            **kwargs
        )
        self.bind(size=self.setter("text_size"))

    def set_bold(self, is_bold):
        """Set the font size to make the text bold or normal"""
        if is_bold:
            self.font_size = FONT.DEFAULT_BOLD
        else:
            self.font_size = FONT.DEFAULT
