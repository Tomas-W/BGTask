from kivy.metrics import dp
from kivy.uix.label import Label
from src.settings import COL, SIZE, SPACE, FONT


class PartitionHeader(Label):
    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint = (1, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.halign = "center"
        self.valign = "center"
        self.font_size = dp(FONT.HEADER)
        self.bold = True
        self.color = COL.HEADER
        
        self.bind(size=self.setter("text_size"))


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
