import os
import enum

from kivy.metrics import dp, sp


class Directories:
    SRC = os.path.dirname(os.path.abspath(__file__))
    ASSETS = os.path.join(SRC, "assets")
    IMG = os.path.join(SRC, ASSETS, "images")

    ALARMS = os.path.join(ASSETS, "alarms")
    RECORDINGS = os.path.join(ASSETS, "recordings")


class Paths(Directories):
    BACK_IMG = os.path.join(Directories.IMG, "back_64.png")
    EDIT_IMG = os.path.join(Directories.IMG, "edit_64.png")
    HISTORY_IMG = os.path.join(Directories.IMG, "history_64.png")

    OPTIONS_IMG = os.path.join(Directories.IMG, "options_64.png")
    OPTIONS_IMG_BLACK = os.path.join(Directories.IMG, "options_black_64.png")
    SCREENSHOT_IMG = os.path.join(Directories.IMG, "screenshot_64.png")
    SETTINGS_IMG = os.path.join(Directories.IMG, "settings_64.png")
    EXIT_IMG = os.path.join(Directories.IMG, "exit_64.png")

    SOUND_IMG = os.path.join(Directories.IMG, "sound_64.png")
    VIBRATE_IMG = os.path.join(Directories.IMG, "vibrate_64.png")
    
    TASK_FILE = os.path.join(Directories.ASSETS, "task_file.json")



class Colors:
    OPAQUE = (0, 0, 0, 0)
    WHITE = (1.0, 1.0, 1.0, 1.0)
    BLACK = (0.0, 0.0, 0.0, 1.0)
    GREEN = (0.0, 1.0, 0.0, 1.0)
    RED = (1.0, 0.0, 0.0, 1.0)

    BG = (0.93, 0.93, 0.93, 1.0)
    
    BAR = (0.2, 0.4, 0.7, 1.0)
    BAR_BUTTON = (0.7, 0.7, 0.7, 0.2)
    SETTINGS_POPUP = (0.44, 0.66, 0.80, 1.0)

    BUTTON_ACTIVE = (0.2, 0.4, 0.7, 0.8)
    BUTTON_INACTIVE = (0.7, 0.7, 0.7, 1.0)

    ERROR = (1, 0.35, 0.35, 0.7)

    CANCEL_BUTTON = (0.7, 0.7, 0.7, 1.0)

    CONFIRM_BUTTON_ACTIVE = (0.25, 0.45, 0.7, 1.0)
    CONFIRM_BUTTON_INACTIVE = (0.45, 0.65, 0.85, 1.0)

    BUTTON_TEXT = (0.0, 0.0, 0.0, 1.0)

    TEXT = (0, 0, 0, 1.0)
    TEXT_GREY = (0.4, 0.4, 0.4, 1.0)

    FIELD_ACTIVE = (0.45, 0.65, 0.95, 0.3)
    FIELD_INACTIVE = (0.5, 0.5, 0.5, 0.3)
    FIELD_ERROR = (1, 0.4, 0.4, 1)
    FIELD_PASSED = (0.2, 0.7, 0.4, 0.8)


class Sizes:
    TEST = dp(40)
    DEFAULT = dp(20)
    DATE_TIME_LABEL = dp(20 * 1.5)

    TOP_BAR_HEIGHT = dp(60)
    TOP_BAR_ICON = dp(TOP_BAR_HEIGHT * 0.4)
    BOTTOM_BAR_HEIGHT = dp(40)

    TOP_BAR_BUTTON_WIDTH = dp(50)

    POPUP_ICON = dp(16)

    HEADER_HEIGHT = dp(25)
    TASK_ITEM_HEIGHT = dp(40)
    TIME_LABEL_HEIGHT = dp(20)

    BUTTON_HEIGHT = dp(60)
    SETTINGS_BUTTON_HEIGHT = dp(40)
    
    CUSTOM_ROW_HEIGHT = dp(40)
    NO_TASKS_LABEL_HEIGHT = dp(100)
    CALENDAR_HEADER_HEIGHT = dp(50)
    CALENDAR_HEIGHT = dp(200)


class Spacing:
    SPACE_XS = dp(5)
    SPACE_S = dp(10)
    SPACE_M = dp(15)
    SPACE_L = dp(25)
    SPACE_XL = dp(40)
    SPACE_XXL = dp(50)
    SPACE_MAX = dp(75)

    TASK_PADDING_X = dp(25)
    TASK_PADDING_Y = dp(20)

    FIELD_PADDING_X = dp(20)       # Padding between bg color and text
    FIELD_PADDING_Y = dp(10)       # Padding between bg color and text
    SCREEN_PADDING_X = dp(20)      # Padding between fields and screen edge
    SCREENSHOT_PADDING_X = dp(30)  # Padding between fields and screen edge
    DAY_SPACING_Y = dp(20)         # Spacing between day groups


class Fonts:
    DEFAULT = sp(20)
    DEFAULT_BOLD = sp(24)
    SMALL = sp(13)

    TOP_BAR = sp(25)
    TOP_BAR_SYMBOL = sp(35)
    BOTTOM_BAR = sp(35)

    TEST = sp(50)

    HEADER = sp(25)
    BUTTON = sp(22)
    BUTTON_FIELD = sp(18)
    BUTTON_SYMBOL = sp(30)

    SETTINGS_HEADER = sp(22)
    SETTINGS_BUTTON = sp(18)
    SETTINGS_BUTTON_SYMBOL = sp(24)
    SETTINGS_BUTTON_FIELD = sp(18)


class Styles:
    RADIUS_S = dp(5)
    RADIUS_M = dp(10)
    RADIUS_L = dp(20)

    BORDER_WIDTH = dp(2)


class Text:
    TYPE_HINT = "Start typing.."
    TYPE_ERROR = "Input is required!"

    NO_TASKS = "Create a new task by clicking the + button!"
    NO_DATE = "No date selected"
    NO_ALARM = "No alarm set"


class Extensions:
    WAV = ".wav"


class StrEnum(str, enum.Enum):
    """String Enum that can be compared directly with strings."""
    pass


class Screens(StrEnum):
    """Screen names used for navigation in the app."""
    START = "START"
    HOME = "HOME"
    NEW_TASK = "NEW_TASK"
    SELECT_DATE = "SELECT_DATE"
    SELECT_ALARM = "SELECT_ALARM"
    SAVED_ALARMS = "SAVED_ALARMS"
    SETTINGS = "SETTINGS"


class Platforms(StrEnum):
    """Supported platforms for the application."""
    ANDROID = "android"
    WINDOWS = "Windows"


class States(StrEnum):
    """UI element states used throughout the application."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"


DIR = Directories()
PATH = Paths()

COL = Colors()



SPACE = Spacing()
FONT = Fonts()
STYLE = Styles()
TEXT = Text()
SIZE = Sizes()
EXT = Extensions()

SCREEN = Screens
PLATFORM = Platforms
STATE = States
