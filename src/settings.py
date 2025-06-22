import enum

from kivy.metrics import dp, sp


class Colors:
    OPAQUE = (0, 0, 0, 0)
    WHITE = (1.0, 1.0, 1.0, 1.0)
    BLACK = (0.0, 0.0, 0.0, 1.0)
    GREEN = (0.0, 1.0, 0.0, 1.0)
    RED = (1.0, 0.0, 0.0, 1.0)

    BG = (0.93, 0.93, 0.93, 1.0)
    BG_POPUP = (0.85, 0.85, 0.85, 1.0)
    
    BAR = (0.2, 0.4, 0.7, 1.0)
    BAR_BUTTON = (0.7, 0.7, 0.7, 0.2)
    SETTINGS_POPUP = (0.44, 0.66, 0.80, 1.0)

    BUTTON_ACTIVE = (0.2, 0.4, 0.7, 0.8)
    BUTTON_INACTIVE = (0.7, 0.7, 0.7, 1.0)

    ERROR = (1, 0.35, 0.35, 0.7)
    SNOOZE = (1, 0.35, 0.35, 1.0)

    CANCEL_BUTTON = (0.7, 0.7, 0.7, 1.0)

    CONFIRM_BUTTON_ACTIVE = (0.25, 0.45, 0.7, 1.0)
    CONFIRM_BUTTON_INACTIVE = (0.45, 0.65, 0.85, 1.0)

    BUTTON_TEXT = (0.0, 0.0, 0.0, 1.0)

    TEXT = (0, 0, 0, 1.0)
    TEXT_GREY = (0.4, 0.4, 0.4, 1.0)

    FIELD_INPUT = (0.45, 0.65, 0.95, 0.3)
    FIELD_TASK = (0.30, 0.40, 0.95, 0.35)
    FIELD_SELECTED = (0.45, 0.65, 0.95, 0.5)
    FIELD_INACTIVE = (0.7, 0.7, 0.7, 0.3)
    FIELD_ERROR = (1, 0.4, 0.4, 1)
    FIELD_PASSED = (0.2, 0.7, 0.4, 0.8)

    TASK_SELECTED = (0.45, 0.65, 0.95, 0.5)
    TASK_ACTIVE = (0.45, 0.65, 0.95, 0.3)
    TASK_INACTIVE = (0.7, 0.7, 0.7, 0.3)
    TASK_INACTIVE_SELECTED = (0.7, 0.7, 0.7, 0.6)


class Sizes:
    TEST = dp(40)
    DEFAULT = dp(20)
    DATE_TIME_LABEL = dp(20 * 1.5)

    TOP_BAR_HEIGHT = dp(60)
    TOP_BAR_ICON = dp(TOP_BAR_HEIGHT * 0.4)
    BOTTOM_BAR_HEIGHT = dp(40)

    TOP_BAR_BUTTON_WIDTH = dp(50)

    FLOATING_CONTAINER_HEIGHT = dp(60)
    FLOATING_CONTAINER_WIDTH = dp(200)

    POPUP_ICON = dp(16)

    HEADER_HEIGHT = dp(25)
    TASK_ITEM_HEIGHT = dp(40)
    TIME_LABEL_HEIGHT = dp(20)

    TASK_POPUP_HEIGHT = sp(200)

    BUTTON_HEIGHT = dp(60)
    SETTINGS_BUTTON_HEIGHT = dp(40)

    ICON_BUTTON_HEIGHT = dp(50)
    
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

    FIELD_PADDING_X = dp(20)
    FIELD_PADDING_Y = dp(10)
    SCREEN_PADDING_X = dp(20)
    SCREENSHOT_PADDING_X = dp(30)
    DAY_SPACING_Y = dp(20)


class Fonts:
    DEFAULT = int(sp(20))
    DEFAULT_BOLD = int(sp(24))
    SMALL = int(sp(16))

    TOP_BAR = int(sp(25))
    TOP_BAR_SYMBOL = int(sp(35))
    BOTTOM_BAR = int(sp(35))

    HEADER = int(sp(25))
    BUTTON = int(sp(22))
    BUTTON_FIELD = int(sp(18))
    BUTTON_SYMBOL = int(sp(30))

    SETTINGS_HEADER = int(sp(22))
    SETTINGS_BUTTON = int(sp(18))
    SETTINGS_BUTTON_SYMBOL = int(sp(24))
    SETTINGS_BUTTON_FIELD = int(sp(18))


class Styles:
    RADIUS_S = dp(5)
    RADIUS_M = dp(10)
    RADIUS_L = dp(20)

    BORDER_WIDTH = dp(2)


class Text:
    TYPE_HINT = "Start typing.."
    TYPE_ERROR = "Input is required!"

    NO_TASKS = "No upcoming tasks!\nPress + to add a new one."
    NO_TASKS_SHORT = "No upcoming tasks!"
    NO_DATE = "No date selected"
    NO_ALARM = "No alarm set"


class Loaded:
    START_SCREEN = False
    HOME_SCREEN = False
    NEW_TASK_SCREEN = False
    SELECT_DATE_SCREEN = False
    SELECT_ALARM_SCREEN = False
    SAVED_ALARMS_SCREEN = False
    SETTINGS_SCREEN = False

    NAVIGATION_MANAGER = False
    TASK_MANAGER = False
    AUDIO_MANAGER = False
    COMMUNICATION_MANAGER = False
    PREFERENCE_MANAGER = False
    POPUP_MANAGER = False

class StrEnum(str, enum.Enum):
    """String Enum that can be compared directly with strings."""
    pass


class Screens(StrEnum):
    """Screen names used for navigation in the app."""
    START = "START"
    HOME = "HOME"
    WALLPAPER = "WALLPAPER"
    NEW_TASK = "NEW_TASK"
    SELECT_DATE = "SELECT_DATE"
    SELECT_ALARM = "SELECT_ALARM"
    SAVED_ALARMS = "SAVED_ALARMS"
    SETTINGS = "SETTINGS"


class States(StrEnum):
    """UI element states used throughout the application."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"


COL = Colors()
FONT = Fonts()
SIZE = Sizes()
SPACE = Spacing()
STYLE = Styles()
TEXT = Text()

LOADED = Loaded()
STATE = States
