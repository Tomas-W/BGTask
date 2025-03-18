import os


class Paths:
    SRC = os.path.dirname(os.path.abspath(__file__))


class Colors:
    OPAQUE = (0, 0, 0, 0)
    # FIELD_BG = (0.77, 0.91, 0.98, 1.0)        # Light Blue - Background for text fields
    FIELD_BG = (50/255, 100/255, 230/255, 0.2)
    BUTTON_ACTIVE = (0.45, 0.65, 0.95, 1.0)   # Blue       - Regular buttons
    TEXT = (0, 0, 0, 1.0)                     # Black       - Regular text
    # BAR = (0.35, 0.55, 0.85, 1.0)      # Dark BLue  - Navigation buttons
    BAR = (50/255, 100/255, 255/255, 1.0)
    BUTTON_INACTIVE = (0.7, 0.7, 0.7, 1.0)    # Grey       - Cancel button and unselected fields
    BUTTON_TEXT = (0.0, 0.0, 0.0, 1.0)        # Whitr      - Button text
    HEADER = (0.4, 0.4, 0.4, 1.0)          # Pale Blue  - Headers
    WHITE = (1.0, 1.0, 1.0, 1.0)              # White      - Pure white
    BG_WHITE = (0.93, 0.93, 0.93, 1.0)        # Light Grey - Background color

    RED = (1.0, 0.0, 0.0, 1.0)


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

    TOP_BAR_SYMBOL = 35
    TOP_BAR = 25
    BOTTOM_BAR = 35

    HEADER = 20
    BUTTON = 20
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


PATH = Paths()
COL = Colors()
SPACE = Spacing()
SIZE = Sizes()
STYLE = Styles()
FONT = Fonts()