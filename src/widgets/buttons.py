from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.button import Button
from kivy.uix.image import Image

from src.settings import COL, SIZE, FONT, STYLE, STATE


class TopBarButton(Button):
    """
    TopBarButton is a button that:
    - Has a background color
    - Has a radius_side (left, none, right) [rounded corners]
    - Has a rounded border
    - Has an image
    """
    def __init__(self, img_path, radius_side, **kwargs):
        super().__init__(
            size_hint=(None, None),
            width=SIZE.TEST,
            height=SIZE.TOP_BAR_HEIGHT,
            background_color=COL.OPAQUE,
            color=COL.WHITE,
            **kwargs
        )
        self.bg_color = COL.BAR_BUTTON
        self.left_radius = [STYLE.RADIUS_L, 0, 0, STYLE.RADIUS_L]
        self.none_radius = [0, 0, 0, 0]
        self.right_radius = [0, STYLE.RADIUS_L, STYLE.RADIUS_L, 0]
        self.radius_side = radius_side
        self.color_instr = None  # Initialize color instruction

        with self.canvas.before:
            self.update_bg_color()  # Create the background color instruction
            if self.radius_side == "left":
                self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.left_radius)
            elif self.radius_side == "none":
                self.bg_rect = Rectangle(pos=self.pos, size=self.size, radius=self.none_radius)
            elif self.radius_side == "right":
                self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.right_radius)
            else:
                raise ValueError(f"Invalid radius side: {self.radius_side}")
            self.bind(pos=self._update, size=self._update)
        
        self.img_path = img_path
        self.image = Image(source=img_path)
        if not self.image.texture:
            raise ValueError(f"Texture not found for {img_path}")
        
        self.icon_size = SIZE.TOP_BAR_ICON
        self.image.size = (self.icon_size, self.icon_size)
        
        self.add_widget(self.image)
        self.bind(pos=self._update_image, size=self._update_image)
        
        self._update_image(self, self.size)
    
    def set_radius_side(self, radius_side):
        """Set the radius side"""
        self.radius_side = radius_side
        if radius_side == "left":
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.left_radius)
        elif radius_side == "none":
            self.bg_rect = Rectangle(pos=self.pos, size=self.size, radius=self.none_radius)
        elif radius_side == "right":
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.right_radius)
        else:
            raise ValueError(f"Invalid radius side: {radius_side}")

    def _update(self, instance, value):
        """Update the background rectangle"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        self.update_bg_color()
    
    def _update_image(self, instance, value):
        """Center the image within the button"""
        self.icon_size = SIZE.TOP_BAR_ICON
        self.image.size = (self.icon_size, self.icon_size)
        
        self.image.pos = (
            self.x + (self.width - self.image.width) / 2,
            self.y + (self.height - self.image.height) / 2
        )
    
    def update_bg_color(self):
        """Update the background color"""
        if self.color_instr is None:
            with self.canvas.before:
                self.color_instr = Color(*self.bg_color)
        else:
            self.color_instr.rgba = self.bg_color  # Update existing color instruction
    
    def set_bg_color(self, color):
        """Set the background color"""
        self.bg_color = color
        self.update_bg_color()
    
    def set_image(self, img_path):
        """Set the image"""
        self.img_path = img_path
        self.remove_widget(self.image)  # Remove old image widget
        self.image = Image(source=img_path)
        if not self.image.texture:
            raise ValueError(f"Texture not found for {img_path}")
        
        self.image.size = (self.icon_size, self.icon_size)
        self.add_widget(self.image)
        self._update_image(self, self.size)  # Position the new image correctly


class TopBarTitle(Button):
    """
    TopBar is the centered navigation button that:
    - Has text
    - Has a background color
    - Can be set unclickable
    """
    def __init__(self, text="", disabled=True,**kwargs):
        super().__init__(
            size_hint=(1, None),
            height=SIZE.TOP_BAR_HEIGHT,
            text=text,
            font_size=FONT.TOP_BAR,
            bold=True,
            color=COL.WHITE,
            disabled_color=COL.WHITE,
            disabled=disabled,
            background_color=COL.OPAQUE,
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def set_disabled(self, disabled: bool):
        """Set the disabled state"""
        self.disabled = disabled
    
    def set_symbol_font_size(self, symbol_font_size: int):
        """Set the symbol font size"""
        self.font_size = symbol_font_size

    def set_text(self, text: str):
        """Set the text"""
        self.text = text


class CustomButton(Button):
    """
    CustomButton is a button that:
    - Has a state (active, inactive, error)
    - Has a background color based on state
    """
    def __init__(self, width: int = 1, color_state: str = STATE.ACTIVE, symbol: bool = False, **kwargs):
        super().__init__(
            size_hint=(width, None),
            height=SIZE.BUTTON_HEIGHT,
            font_size=FONT.BUTTON if not symbol else FONT.BUTTON_SYMBOL,
            bold=True if symbol else False,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            **kwargs
        )
        
        # Set default colors - can be overridden by subclasses
        self._init_colors()
        self.color_state = color_state
        self.disabled_color = COL.WHITE
        self.always_clickable = False  # New property
        
        # Background color - will be set based on state
        with self.canvas.before:
            self.color_instr = Color(1, 1, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[STYLE.RADIUS_M])
            self.bind(pos=self._update, size=self._update)
        
        # Apply the initial state
        self._init_state()
    
    def _init_colors(self):
        """Initialize the button colors - can be overridden by subclasses"""
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE
        self.color_error = COL.ERROR
    
    def _init_state(self):
        if self.color_state == STATE.ACTIVE:
            self.set_active_state()
        elif self.color_state == STATE.INACTIVE:
            self.set_inactive_state()
        elif self.color_state == STATE.ERROR:
            self.set_error_state()
        else:
            raise ValueError(f"Invalid state: {self.color_state}")

    def _update(self, instance, value):
        """Update background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def set_error_state(self):
        self.color_state = STATE.ERROR
        self.color_instr.rgba = self.color_error
        if not self.always_clickable:
            self.disabled = True
    
    def set_active_state(self):
        self.color_state = STATE.ACTIVE
        self.color_instr.rgba = self.color_active
        self.disabled = False
    
    def set_inactive_state(self):
        self.color_state = STATE.INACTIVE
        self.color_instr.rgba = self.color_inactive
        if not self.always_clickable:
            self.disabled = True

    def set_text(self, text):
        self.text = text
    
    def set_disabled(self, value):
        self.disabled = value


class CustomCancelButton(CustomButton):
    """
    CustomCancelButton is a Cancel button that:
    - Inherits from CustomButton
    - Only differs in color
    - Does not use states
    """
    def __init__(self, width: int = 1, symbol: bool = False, color_state: str = STATE.ACTIVE, **kwargs):
        super().__init__(
            width=width,
            color_state=color_state,
            symbol=symbol,
            **kwargs
        )
        self.disabled_color = COL.WHITE
    
    def _init_colors(self):
        """Override the button colors"""
        self.color_active = COL.CANCEL_BUTTON
        self.color_inactive = COL.CANCEL_BUTTON
        self.color_error = COL.CANCEL_BUTTON


class CustomConfirmButton(CustomButton):
    """
    CustomConfirmButton is a Confirm button that:
    - Inherits from CustomButton
    - Only differs in color
    """
    def __init__(self, width: int = 1, color_state: str = STATE.ACTIVE, symbol: bool = False, **kwargs):
        super().__init__(
            width=width,
            color_state=color_state,
            symbol=symbol,
            **kwargs
        )
        self.disabled_color = COL.WHITE
        self.always_clickable = True
        self.disabled = False
    
    def _init_colors(self):
        """Override the button colors"""
        self.color_active = COL.CONFIRM_BUTTON_ACTIVE
        self.color_inactive = COL.CONFIRM_BUTTON_INACTIVE
        self.color_error = COL.ERROR


class CustomSettingsButton(CustomButton):
    """
    CustomSettingsButton is a button that:
    - Inherits styling and functionality from CustomButton
    - Is 2/3 the height of the CustomButton
    - Always remains clickable regardless of visual state
    """
    def __init__(self, width: int, symbol: bool = False, color_state: str = STATE.INACTIVE, **kwargs):
        super().__init__(
            width=width,
            symbol=symbol,
            color_state=color_state,
            **kwargs
        )
        self.height = SIZE.SETTINGS_BUTTON_HEIGHT
        self.font_size = FONT.SETTINGS_BUTTON if not symbol else FONT.SETTINGS_BUTTON_SYMBOL
        self.always_clickable = True  # Set property to keep clickable
        self.disabled = False  # Ensure it's enabled
