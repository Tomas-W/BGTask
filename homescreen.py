from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock

import settings
from taskmanager import TaskManager

class TaskGroup(BoxLayout):
    """Widget to display tasks grouped by date"""
    def __init__(self, date_str, tasks, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        # Add date header
        date_label = Label(
            text=date_str,
            size_hint=(1, None),
            height=dp(settings.HEADER_HEIGHT),
            halign="left",
            font_size=dp(settings.HEADER_FONT_SIZE),
            bold=True,
            color=settings.HEADER_COLOR,
            padding=[0, 0, 0, 0]  # Use consistent field padding
        )
        date_label.bind(size=date_label.setter("text_size"))
        self.add_widget(date_label)
        
        # Spacer below date label (height also added to overall height)
        spacer = BoxLayout(
            size_hint_y=None,
            height=dp(settings.SPACE_Y_XS)  # linked with update_group_height
        )
        self.add_widget(spacer)
        
        # Create a container for tasks with background
        self.tasks_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(settings.SPACE_Y_L),  # Spacing between tasks
            padding=[0, dp(settings.SPACE_Y_M), 0, dp(settings.SPACE_Y_M)]  # Vertical padding
        )
        
        # Bind the container's height to its children
        self.tasks_container.bind(minimum_height=self.tasks_container.setter("height"))
        
        # Set background for the tasks container with rounded corners
        with self.tasks_container.canvas.before:
            Color(*settings.LIGHT_BLUE)
            self.bg_rect = RoundedRectangle(
                pos=self.tasks_container.pos, 
                size=self.tasks_container.size,
                radius=[dp(settings.CORNER_RADIUS)]
            )
            self.tasks_container.bind(pos=self.update_bg_rect, size=self.update_bg_rect)
        
        # Add task items
        for task in tasks:
            self.add_task_item(task)
            
        self.add_widget(self.tasks_container)
        
        # Update overall height
        self.height = date_label.height + self.tasks_container.height  # Remove extra spacing
        
        # Bind our height to update when tasks_container height changes
        self.tasks_container.bind(height=self.update_group_height)
    
    def update_group_height(self, instance, value):
        """Update the overall height when tasks_container height changes"""
        # Spacer + DATE_HEADER_HEIGHT for date_label + tasks_container height
        self.height = dp(settings.SPACE_Y_XS) + dp(settings.HEADER_HEIGHT) + value
    
    def update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def add_task_item(self, task):
        """Add a task item widget"""
        # Create a container for both time and message with consistent padding
        task_layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(settings.TASK_ITEM_HEIGHT),
            padding=[0, 0, 0, 0],  # No padding at this level
        )
        
        # Time label with the same indentation as message
        time_label = Label(
            text=task.get_time_str(),
            size_hint=(1, None),
            height=dp(settings.TIME_LABEL_HEIGHT),
            halign="left",
            font_size=dp(settings.DEFAULT_FONT_SIZE),
            bold=True,
            color=settings.TEXT_COLOR,
            padding=[dp(settings.FIELD_PADDING_X), 0, dp(settings.FIELD_PADDING_X), 0]  # Use FIELD_PADDING_X for indentation
        )
        time_label.bind(size=time_label.setter("text_size"))
        
        # Task message label with proper text wrapping
        message_label = Label(
            text=task.message,
            size_hint=(1, None),
            height=dp(settings.MESSAGE_LABEL_HEIGHT),
            halign="left",
            valign="top",
            font_size=dp(settings.DEFAULT_FONT_SIZE),
            color=settings.TEXT_COLOR,
            padding=[dp(settings.FIELD_PADDING_X), dp(0)]  # Use FIELD_PADDING_X for indentation
        )
        
        # Improved text wrapping and height calculation
        def update_text_size(instance, value):
            # Set text width to parent width minus padding
            width = value[0]
            instance.text_size = (width, None)  # None height lets text determine needed height
            
            # After text renders with new size, check text height
            def adjust_height(dt):
                # Get actual height needed for text content
                needed_height = max(dp(settings.MESSAGE_LABEL_HEIGHT), instance.texture_size[1])
                instance.height = needed_height
                
                # Update overall task_layout height
                task_layout.height = time_label.height + instance.height
            
            # Schedule the height adjustment for next frame
            Clock.schedule_once(adjust_height, 0)
        
        message_label.bind(size=update_text_size)
        
        task_layout.add_widget(time_label)
        task_layout.add_widget(message_label)
        self.tasks_container.add_widget(task_layout)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Task manager
        self.task_manager = TaskManager()
        
        # Root layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Top bar with + button
        self.top_bar = BoxLayout(
            size_hint=(1, None),
            height=dp(settings.NAV_HEIGHT)
        )
        
        # Top bar background
        with self.top_bar.canvas.before:
            Color(*settings.DARK_BLUE)
            self.top_rect = Rectangle(pos=self.top_bar.pos, size=self.top_bar.size)
            self.top_bar.bind(pos=self.update_top_rect, size=self.update_top_rect)
        
        # Add button
        self.add_button = Button(
            text="+",
            font_size=dp(settings.NAV_FONT_SIZE),
            bold=True,
            background_color=(0, 0, 0, 0),
            color=settings.WHITE,
            size_hint=(None, None),
            size=(dp(settings.ADD_BUTTON_SIZE), dp(settings.ADD_BUTTON_SIZE)),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        self.add_button.bind(on_press=self.go_to_task_screen)
        self.top_bar.add_widget(self.add_button)
        
        # Content area
        self.content_layout = BoxLayout(orientation="vertical")
        
        # Scroll view for tasks
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True
        )
        
        # Container for task groups
        self.task_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(settings.SPACE_Y_XL),  # Larger spacing between day groups
            padding=[dp(settings.SCREEN_PADDING_X), dp(0), 
                     dp(settings.SCREEN_PADDING_X), dp(0)]  # Padding around all content
        )
        self.task_container.bind(minimum_height=self.task_container.setter("height"))
        
        # Background color
        with self.layout.canvas.before:
            Color(*settings.BG_WHITE)
            self.bg_rect = Rectangle(pos=self.layout.pos, size=self.layout.size)
            self.layout.bind(pos=self.update_bg_rect, size=self.update_bg_rect)
        
        # Assemble the layout
        self.scroll_view.add_widget(self.task_container)
        self.content_layout.add_widget(self.scroll_view)
        
        self.layout.add_widget(self.top_bar)
        
        # Add spacer after top bar
        spacer = BoxLayout(
            size_hint_y=None,
            height=dp(settings.SPACE_Y_XL)
        )
        self.layout.add_widget(spacer)
        
        self.layout.add_widget(self.content_layout)
        
        self.add_widget(self.layout)
    
    def update_top_rect(self, instance, value):
        self.top_rect.pos = instance.pos
        self.top_rect.size = instance.size
    
    def update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def go_to_task_screen(self, instance):
        self.manager.current = "task"
    
    def load_tasks(self):
        """Load and display tasks"""
        self.task_manager.load_tasks()
        self.update_task_display()
    
    def update_task_display(self):
        """Update the task display with current tasks"""
        self.task_container.clear_widgets()
        
        # Get tasks grouped by date
        task_groups = self.task_manager.get_tasks_by_date()
        
        if not task_groups:
            no_tasks_label = Label(
                text="No tasks yet. Add one by tapping the + button!",
                size_hint=(1, None),
                height=dp(settings.NO_TASKS_LABEL_HEIGHT),
                color=settings.TEXT_COLOR
            )
            self.task_container.add_widget(no_tasks_label)
            return
        
        # Add task groups to display
        for group in task_groups:
            task_group = TaskGroup(
                date_str=group["date"],
                tasks=group["tasks"],
                size_hint=(1, None)  # Allow height to be calculated
            )
            self.task_container.add_widget(task_group)
    
    def on_enter(self):
        """Called when screen is entered"""
        # Update task display whenever we return to this screen
        self.update_task_display() 