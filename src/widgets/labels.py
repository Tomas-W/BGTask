from kivy.uix.label import Label

from src.settings import COL, SIZE, FONT


class PartitionHeader(Label):
    """
    PartitionHeader is a header for a partition that:
    - Can be aligned (center by default)
    """
    def __init__(self, text: str, halign: str = "center", valign: str = "center", **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, 1),
            height=SIZE.HEADER_HEIGHT,
            halign=halign,
            valign=valign,
            font_size=FONT.HEADER,
            bold=True,
            color=COL.TEXT_GREY,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))
    
    def set_text(self, text):
        self.text = text


class ButtonFieldLabel(Label):
    """
    ButtonFieldLabel is a label for a CustomButton
    """
    def __init__(self, text="", **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            color=COL.TEXT,
            font_size=FONT.BUTTON_FIELD,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))


class SettingsFieldLabel(Label):
    """
    SettingsFieldLabel is a label for a SettingsField
    """
    def __init__(self, text="", **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            color=COL.TEXT,
            font_size=FONT.BUTTON_FIELD,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))
