from kivy.effects.scroll import ScrollEffect
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from src.settings import COL, SIZE, SPACE, FONT, STYLE


class BaseLayout(BoxLayout):
    """
    Base layout for all screens that:
    - Contains a TopBar, ScrollContainer and a BottomBar
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"top": 1, "center_x": 0.5},
            **kwargs
        )


class MainContainer(BoxLayout):
    """
    Main container is the base for the ScrollContainer that:
    - Sets spacing between its children
    - Sets padding between the screen edges and itself
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=SPACE.SPACE_XL,
            padding=[SPACE.SCREEN_PADDING_X, SPACE.SPACE_XXL],
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))
        
        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class StartContainer(BoxLayout):
    """
    Start container is the base for the StartScreen that:
    - Contains a MainContainer
    - Has a background color
    - Sets spacing between its children

    """
    def __init__(self, parent_screen, **kwargs):
        self.container = MainContainer()
        self.container.spacing = SPACE.SPACE_MAX
        super().__init__(
            orientation="vertical",
            **kwargs
        )
        self.parent_screen = parent_screen

        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)

        self.scroll_view = ScrollView(
            do_scroll_x=True,
            do_scroll_y=True,
            scroll_wheel_distance=60,
            effect_cls=ScrollEffect,
        )
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)
        
    def _update(self, instance, value):
        """Update the background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def on_touch_down(self, touch):
        # Store the initial touch position
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        # Calculate distance moved
        delta_x = touch.x - self.touch_start_x
        delta_y = touch.y - self.touch_start_y
        
        # Is swipe significant enough
        if abs(delta_x) > 10 or abs(delta_y) > 10:
            # Horizontal
            if abs(delta_x) > abs(delta_y):
                if delta_x > 0:
                    self.on_swipe_right()
                else:
                    self.on_swipe_left()
            # Vertical
            else:
                if delta_y > 0:
                    self.on_swipe_up()
                else:
                    self.on_swipe_down()
        
        return super().on_touch_up(touch)
    
    def on_swipe_right(self):
        if self.parent_screen:
            self.parent_screen.navigate_to_home_screen("right")
    
    def on_swipe_left(self):
        if self.parent_screen:
            self.parent_screen.navigate_to_home_screen("left")
    
    def on_swipe_up(self):
        pass
    
    def on_swipe_down(self):
        pass


class ScrollContainer(BoxLayout):
    """
    Scroll container is the base for all content that:
    - Contains a MainContainer
    - Sets the background color
    - Handles scrolling
    """
    def __init__(self,
                parent_screen,
                allow_scroll_y,
                allow_scroll_x,
                **kwargs
        ):
        self.container = MainContainer()
        super().__init__(
            orientation="horizontal",
            **kwargs
        )
        self.parent_screen = parent_screen
        
        with self.canvas.before:
            Color(*COL.BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)

        self.scroll_view = ScrollView(
            do_scroll_x=allow_scroll_x,
            do_scroll_y=allow_scroll_y,
            scroll_wheel_distance=80,
            effect_cls=ScrollEffect,
        )
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)
    
    def _update(self, instance, value):
        """Update the background"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class TopBarContainer(BoxLayout):
    """
    Top bar container is the base for the TopBar that:
    - Sets a background color
    """
    def __init__(self, **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=SIZE.TOP_BAR_HEIGHT,
            **kwargs
        )
        
        with self.canvas.before:
            Color(*COL.BAR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update, size=self._update)
    
    def _update(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class Partition(BoxLayout):
    """
    Partition is the base for all content with similar functionality that:
    - Sets spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            spacing=SPACE.SPACE_S,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class BorderedPartition(Partition):
    """
    BorderedPartition is a Partition that:
    - Has a border in TEXT color
    - Can have rounded corners at top or bottom
    - Maintains same spacing and functionality as Partition
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_color = COL.BLACK
        self.border_color_active = COL.BUTTON_ACTIVE

        self.border_radius = STYLE.RADIUS_M
        self._current_radius = [self.border_radius] * 4

        with self.canvas.before:
            # Border - initially visible
            self.border_color_instr = Color(*self.border_color)
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1],
                    self.size[0], self.size[1],
                    self._current_radius[0]
                ),
                width=1
            )
            self.bind(pos=self._update, size=self._update)

    def _update(self, instance, value):
        """Update the border rectangle"""
        self.border_rect.rounded_rectangle = (
            instance.pos[0], instance.pos[1],
            instance.size[0], instance.size[1],
            self._current_radius[0]
        )

    def set_active(self):
        """Set border color to active"""
        self.border_color_instr.rgba = self.border_color_active

    def set_inactive(self):
        """Set border color to default (inactive)"""
        self.border_color_instr.rgba = self.border_color


class CustomButtonRow(BoxLayout):
    """
    CustomButtonRow is the base for a row of CustomButtons that:
    - Contains CustomButtons
    - Has spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            pos_hint={"center_y": 0.5, "center_x": 0.5},
            height=SIZE.BUTTON_HEIGHT,
            spacing=SPACE.SPACE_M,
            **kwargs
        )


class CustomIconButtonRow(BoxLayout):
    """
    CustomIconButtonRow is the base for a row of CustomIconButtons that:
    - Contains IconButtons arranged horizontally
    - Dynamically adjusts spacing based on number of icons
    - Centers icons within the container
    - Adapts to different screen sizes and platforms
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            pos_hint={"center_y": 0.5, "center_x": 0.5},
            height=SIZE.ICON_BUTTON_HEIGHT,
            padding=[SPACE.SPACE_L, 0],
            **kwargs
        )
        self.bind(
            minimum_height=self.setter("height"),
            size=self._update_spacing,
            children=self._update_spacing
        )
    
    def _update_spacing(self, *args):
        """Dynamically update spacing based on container width and number of children"""
        if not self.children:
            return
        
        # Calculate total width available for spacing
        padding = self.padding[0] * 2
        total_width = self.width - padding
        num_children = len(self.children)
        total_children_width = num_children * SIZE.ICON_BUTTON_HEIGHT
        
        if num_children > 1:
            # Calculate spacing needed between each child
            available_space = total_width - total_children_width
            self.spacing = available_space / (num_children - 1)
        else:
            self.spacing = 0


class CustomSettingsButtonRow(CustomButtonRow):
    """
    CustomSettingsButtonRow is the base for a row of CustomSettingsButtons that:
    - Contains CustomSettingsButtons
    - Has spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs
        )
        self.height = SIZE.SETTINGS_BUTTON_HEIGHT

class CustomRow(BoxLayout):
    """
    CustomRow is the base for a row of widgets that:
    - Contains widgets
    - Has spacing between its children
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(0.5, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            height=2 * FONT.HEADER,
            spacing=SPACE.SPACE_XS,
            **kwargs
        )
