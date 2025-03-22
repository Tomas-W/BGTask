from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label

from src.settings import COL, FONT, SIZE


class DateTimeLabel(ButtonBehavior, Label):
    """Label that behaves like a button"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = FONT.DEFAULT
        self.color = COL.TEXT_GREY
        self.bold = True
        self.size_hint_y = None
        self.height = SIZE.DATE_TIME_LABEL
        self.halign = "center"
        self.valign = "middle"
        self.bind(size=self.setter("text_size"))

    def set_bold(self, is_bold):
        """Set the font size to make the text bold or normal"""
        if is_bold:
            self.font_size = FONT.DEFAULT_BOLD
        else:
            self.font_size = FONT.DEFAULT
