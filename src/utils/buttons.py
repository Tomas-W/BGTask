from kivy.animation import Animation, AnimationTransition
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.button import Button
from kivy.uix.image import Image

from src.settings import COL, SIZE, SPACE, FONT, STYLE, STATE


class TopBarButton(Button):
    """
    TopBarButton is a button that:
    - Has a side (left, right)
    - Has a background color
    - Has a rounded border
    - Has an image
    """
    def __init__(self, img_path, side, **kwargs):
        super().__init__(
            size_hint=(0.25, None),
            height=SIZE.TOP_BAR_HEIGHT,
            background_color=COL.OPAQUE,
            color=COL.WHITE,
            **kwargs
        )
        if side == "left":
            self.radius = [0, STYLE.RADIUS_L, STYLE.RADIUS_L, 0]
        elif side == "right":
            self.radius = [STYLE.RADIUS_L, 0, 0, STYLE.RADIUS_L]

        with self.canvas.before:
            Color(*COL.BAR_BUTTON)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
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

    def _update(self, instance, value):
        """Update the background rectangle"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _update_image(self, instance, value):
        """Center the image within the button"""
        self.icon_size = SIZE.TOP_BAR_ICON
        self.image.size = (self.icon_size, self.icon_size)
        
        self.image.pos = (
            self.x + (self.width - self.image.width) / 2,
            self.y + (self.height - self.image.height) / 2
        )

class CustomButton(Button):
    """
    CustomButton is a button that:
    - Has a state (active, inactive, error)
    - Has a background color based on state
    """
    def __init__(self, width: int, color_state: str, symbol: bool = False, **kwargs):
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


class TopBar(Button):
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
