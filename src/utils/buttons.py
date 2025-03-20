from kivy.animation import Animation, AnimationTransition
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.button import Button
from src.settings import COL, SIZE, SPACE, FONT, STYLE


class CustomButton(Button):
    """Button with state management"""
    # Define state constants
    STATE_ACTIVE = "active"
    STATE_INACTIVE = "inactive" 
    STATE_ERROR = "error"
    
    def __init__(self, width: int, color_state: str, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (width, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.font_size = dp(FONT.BUTTON)
        self.color = COL.WHITE
        self.background_color = COL.OPAQUE
        
        self.radius = [dp(STYLE.CORNER_RADIUS)]
        self.color_active = COL.BUTTON_ACTIVE
        self.color_inactive = COL.BUTTON_INACTIVE
        self.color_error = COL.BUTTON_ERROR
        
        # Set initial state
        self.color_state = color_state
        
        # Create the canvas instructons, but don't set color yet
        with self.canvas.before:
            self.color_instr = Color(1, 1, 1)  # Temporary color
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            self.bind(pos=self._update, size=self._update)
        
        # Apply the initial state
        if self.color_state == self.STATE_ACTIVE:
            self.set_active_state()
        elif self.color_state == self.STATE_INACTIVE:
            self.set_inactive_state()
        elif self.color_state == self.STATE_ERROR:
            self.set_error_state()
        else:
            raise ValueError(f"Invalid state: {self.color_state}")

    def _update(self, instance, value):
        """Update background rectangle on resize/reposition"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def set_error_state(self):
        """Set button to error state"""
        self.color_state = self.STATE_ERROR
        self.color_instr.rgba = self.color_error
    
    def set_active_state(self):
        """Set button back to normal state"""
        self.color_state = self.STATE_ACTIVE
        self.color_instr.rgba = self.color_active
    
    def set_inactive_state(self):
        """Set button to inactive state"""
        self.color_state = self.STATE_INACTIVE
        self.color_instr.rgba = self.color_inactive


class TopBar(Button):
    def __init__(self, text="", button=True,**kwargs):
        super().__init__(
            size_hint=(1, None),
            height=dp(SIZE.TOP_BAR_HEIGHT),
            text=text,
            font_size=dp(FONT.TOP_BAR_SYMBOL) if button else dp(FONT.TOP_BAR),
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
    def __init__(self, text="", **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=dp(SIZE.BOTTOM_BAR_HEIGHT),
            padding=[0, dp(SPACE.SPACE_Y_M), 0, 0],
            pos_hint={"center_x": 0.5, "y": -0.15},  # Just below screen
            text=text,
            font_size=dp(FONT.BOTTOM_BAR),
            bold=True,
            color=COL.WHITE,
            background_color=COL.OPAQUE,
            opacity=0,  # Start hidden
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
        
        self.visible = False
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def show(self, *args):
        """Animate the bottom bar into view with smooth sliding"""
        if self.visible:
            return
            
        self.visible = True
        
        # Slide up and fade in
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
        
        # Slide down and fade out
        anim = Animation(
            opacity=0, 
            pos_hint={"center_x": 0.5, "y": -0.15}, 
            duration=0.3,
            transition=AnimationTransition.in_quad
        )
        anim.start(self)
