import os


class Paths:
    SRC = os.path.dirname(os.path.abspath(__file__))


class Colors:
    OPAQUE = (0, 0, 0, 0)
    WHITE = (1.0, 1.0, 1.0, 1.0)
    BLACK = (0.0, 0.0, 0.0, 1.0)

    BG = (0.93, 0.93, 0.93, 1.0)
    
    BUTTON_ACTIVE = (0.2, 0.4, 0.7, 1.0)
    BUTTON_INACTIVE = (0.7, 0.7, 0.7, 1.0)
    BUTTON_ERROR = (0.6, 0, 0, 0.7)
    BUTTON_TEXT = (0.0, 0.0, 0.0, 1.0)

    TEXT = (0, 0, 0, 1.0)
    ERROR_TEXT = (1.0, 0.0, 0.0, 0.8)
    HEADER = (0.4, 0.4, 0.4, 1.0)
    FIELD_ACTIVE = (0.45, 0.65, 0.95, 0.3)
    FIELD_INACTIVE = (0.5, 0.5, 0.5, 0.3)
    FIELD_ERROR = (1, 0.6, 0.6, 1.0)
    

class Spacing:
    SPACE_Y_XS = 5
    SPACE_Y_S = 10
    SPACE_Y_M = 15
    SPACE_Y_L = 30
    SPACE_Y_XL = 40
    SPACE_Y_XXL = 50
    FIELD_PADDING_X = 20   # Padding between bg color and text
    FIELD_PADDING_Y = 10   # Padding between bg color and text
    SCREEN_PADDING_X = 20  # Padding between fields and screen edge
    DAY_SPACING_Y = 20     # Spacing between day groups


class Fonts:
    DEFAULT = 16

    TOP_BAR = 25
    TOP_BAR_SYMBOL = 35
    BOTTOM_BAR = 35

    HEADER = 20
    BUTTON = 18
    CALENDAR = 18


class Sizes:
    TOP_BAR_HEIGHT = 50
    BOTTOM_BAR_HEIGHT = 30

    HEADER_HEIGHT = Fonts.HEADER
    TASK_ITEM_HEIGHT = 40 
    TIME_LABEL_HEIGHT = 20
    MESSAGE_LABEL_HEIGHT = Fonts.DEFAULT * 1.3

    BUTTON_HEIGHT = 60
    NO_TASKS_LABEL_HEIGHT = 100
    CALENDAR_HEADER_HEIGHT = 50
    CALENDAR_HEIGHT = 300


class Styles:
    CORNER_RADIUS = 10


class Text:
    TYPE_HINT = "Start typing.."
    TYPE_ERROR = "Input is required!"


PATH = Paths()
COL = Colors()
SPACE = Spacing()
SIZE = Sizes()
STYLE = Styles()
FONT = Fonts()
TEXT = Text()