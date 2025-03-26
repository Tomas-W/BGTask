from kivy.animation import Animation, AnimationTransition
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout

from src.settings import COL, SIZE, SPACE, FONT, STYLE, STATE


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


class TopBarTitle(Button):
    """
    TopBar is the centered navigation button that:
    - Has text
    - Has a background color
    - Can be set unclickable
    """
    def __init__(self, text="", button=True,**kwargs):
        super().__init__(
            size_hint=(1, None),
            height=SIZE.TOP_BAR_HEIGHT,
            text=text,
            font_size=FONT.TOP_BAR_SYMBOL if button else FONT.TOP_BAR,
            bold=True,
            color=COL.WHITE,
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


class BottomBar(Button):
    """
    BottomBar is the bottom navigation button that:
    - Brings the user back to the top of the screen
    - Has a background color
    - Has a symbol
    - Is initially hidden
    - Has an animation
    """
    def __init__(self, text="", **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=SIZE.BOTTOM_BAR_HEIGHT,
            padding=[0, SPACE.SPACE_M, 0, 0],
            pos_hint={"center_x": 0.5, "y": -0.15},  # Just below screen
            text=text,
            font_size=FONT.BOTTOM_BAR,
            bold=True,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            opacity=0,  # Start hidden
            **kwargs
        )
        self.visible = False

        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def show(self, *args):
        """Animate the bottom bar into view with smooth sliding"""
        if self.visible:
            return
            
        self.visible = True
        anim = Animation(
            opacity=1, 
            pos_hint={"center_x": 0.5, "y": 0}, 
            duration=0.3,
            transition=AnimationTransition.out_quad
        )
        anim.start(self)
    
    def hide(self, *args):
        """Animate the bottom bar out of view with smooth sliding"""
        if not self.visible:
            return
            
        self.visible = False        
        anim = Animation(
            opacity=0, 
            pos_hint={"center_x": 0.5, "y": -0.15}, 
            duration=0.3,
            transition=AnimationTransition.in_quad
        )
        anim.start(self)


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
        
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE
        self.color_error = COL.BUTTON_ERROR
        self.color_state = color_state
        
        # Background color - will be set based on state
        with self.canvas.before:
            self.color_instr = Color(1, 1, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[STYLE.RADIUS_M])
            self.bind(pos=self._update, size=self._update)
        
        # Apply the initial state
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
    
    def set_active_state(self):
        self.color_state = STATE.ACTIVE
        self.color_instr.rgba = self.color_active
    
    def set_inactive_state(self):
        self.color_state = STATE.INACTIVE
        self.color_instr.rgba = self.color_inactive
    
    def set_text(self, text):
        self.text = text
    
    def set_disabled(self, bool: bool):
        self.disabled = bool


class CustomSettingsButton(CustomButton):
    """
    CustomSettingsButton is a button that:
    - Inherits styling and functionality from CustomButton
    - Is 2/3 the height of the CustomButton
    """
    def __init__(self, width: int, symbol: bool = False, **kwargs):
        super().__init__(
            width=width,
            symbol=symbol,
            **kwargs
        )
        self.height = SIZE.SETTINGS_BUTTON_HEIGHT
        self.font_size = FONT.SETTINGS_BUTTON if not symbol else FONT.SETTINGS_BUTTON_SYMBOL
