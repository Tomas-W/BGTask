import os

from kivy.metrics import dp, sp


class Paths:
    SRC = os.path.dirname(os.path.abspath(__file__))
    IMG = os.path.join(SRC, "images")

    EXIT_IMG = os.path.join(IMG, "exit_64.png")
    SETTINGS_IMG = os.path.join(IMG, "settings_64.png")
    BACK_IMG = os.path.join(IMG, "back_64.png")

    TASK_FILE = "task_file.json"

class Colors:
    OPAQUE = (0, 0, 0, 0)
    WHITE = (1.0, 1.0, 1.0, 1.0)
    BLACK = (0.0, 0.0, 0.0, 1.0)

    BG = (0.93, 0.93, 0.93, 1.0)
    
    BAR = (0.2, 0.4, 0.7, 1.0)
    BAR_BUTTON = (0.7, 0.7, 0.7, 0.2)

    BUTTON_ACTIVE = (0.2, 0.4, 0.7, 0.8)
    BUTTON_INACTIVE = (0.7, 0.7, 0.7, 1.0)
    BUTTON_ERROR = (0.6, 0, 0, 0.7)
    BUTTON_TEXT = (0.0, 0.0, 0.0, 1.0)

    TEXT = (0, 0, 0, 1.0)
    TEXT_GREY = (0.4, 0.4, 0.4, 1.0)
    ERROR_TEXT = (1.0, 0.0, 0.0, 0.8)
    FIELD_ACTIVE = (0.45, 0.65, 0.95, 0.3)
    FIELD_INACTIVE = (0.5, 0.5, 0.5, 0.3)
    FIELD_ERROR = (1, 0.6, 0.6, 1.0)
    

class Spacing:
    SPACE_XS = dp(5)
    SPACE_S = dp(10)
    SPACE_M = dp(15)
    SPACE_L = dp(25)
    SPACE_XL = dp(40)
    SPACE_XXL = dp(50)
    SPACE_MAX = dp(75)
    FIELD_PADDING_X = dp(20)   # Padding between bg color and text
    FIELD_PADDING_Y = dp(10)   # Padding between bg color and text
    SCREEN_PADDING_X = dp(20)  # Padding between fields and screen edge
    DAY_SPACING_Y = dp(20)     # Spacing between day groups


class Fonts:
    DEFAULT = sp(20)
    DEFAULT_BOLD = sp(24)
    SMALL = sp(13)

    TOP_BAR = sp(25)
    TOP_BAR_SYMBOL = sp(35)
    BOTTOM_BAR = sp(35)

    HEADER = sp(25)
    BUTTON = sp(18)
    BUTTON_SYMBOL = sp(30)


class Sizes:
    DEFAULT = dp(20)
    DATE_TIME_LABEL = dp(20 * 1.5)

    TOP_BAR_HEIGHT = dp(60)
    TOP_BAR_ICON = dp(TOP_BAR_HEIGHT * 0.4)
    BOTTOM_BAR_HEIGHT = dp(40)

    HEADER_HEIGHT = dp(25)
    TASK_ITEM_HEIGHT = dp(40)
    TIME_LABEL_HEIGHT = dp(20)

    BUTTON_HEIGHT = dp(60)
    NO_TASKS_LABEL_HEIGHT = dp(100)
    CALENDAR_HEADER_HEIGHT = dp(50)
    CALENDAR_HEIGHT = dp(200)


class Styles:
    RADIUS_S = dp(5)
    RADIUS_M = dp(10)
    RADIUS_L = dp(20)

    BORDER_WIDTH = dp(2)


class Text:
    TYPE_HINT = "Start typing.."
    TYPE_ERROR = "Input is required!"
    NO_TASKS = "Create a new task by clicking the + button!"


class Screens:
    HOME = "HOME"
    NEW_TASK = "NEW_TASK"
    SELECT_DATE = "SELECT_DATE"


class States:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"


PATH = Paths()
COL = Colors()
SPACE = Spacing()
SIZE = Sizes()
STYLE = Styles()
FONT = Fonts()
TEXT = Text()
SCREEN = Screens()
STATE = States()