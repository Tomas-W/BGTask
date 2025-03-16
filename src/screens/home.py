from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from src.utils.taskmanager import TaskManager
from src.utils.widgets import TopBar, BottomBar, ScrollContainer
from src.settings import COL, SPACE, SIZE, STYLE


class TaskGroup(BoxLayout):
    """
    Displays tasks grouped by date.
    Day header on top, tasks below with blue bg.
    """
    def __init__(self, date_str, tasks, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        day_header = Label(
            text=date_str,
            size_hint=(1, None),
            height=dp(SIZE.HEADER_HEIGHT),
            halign="left",
            font_size=dp(SIZE.HEADER_FONT),
            bold=True,
            color=COL.HEADER,
        )
        day_header.bind(size=day_header.setter("text_size"))
        self.add_widget(day_header)
        
        # Spacer below date label
        spacer = BoxLayout(
            size_hint_y=None,
            height=dp(SPACE.SPACE_Y_XS)  # linked with update_group_height
        )
        self.add_widget(spacer)
        
        # Tasks container
        self.tasks_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SPACE.SPACE_Y_L),
            padding=[0, dp(SPACE.SPACE_Y_M), 0, dp(SPACE.SPACE_Y_M)]
        )
        self.tasks_container.bind(minimum_height=self.tasks_container.setter("height"))
        # Set background
        with self.tasks_container.canvas.before:
            Color(*COL.FIELD_BG)
            self.bg_rect = RoundedRectangle(
                pos=self.tasks_container.pos, 
                size=self.tasks_container.size,
                radius=[dp(STYLE.CORNER_RADIUS)]
            )
            self.tasks_container.bind(pos=self.update_bg_rect, size=self.update_bg_rect)
        
        for task in tasks:
            self.add_task_item(task)
            
        self.add_widget(self.tasks_container)
        
        self.height = day_header.height + self.tasks_container.height  # Remove extra spacing
        self.tasks_container.bind(height=self.update_group_height)
    
    def update_group_height(self, instance, value):
        """Update the overall height when tasks_container height changes"""
        self.height = dp(SPACE.SPACE_Y_XS) + dp(SIZE.HEADER_HEIGHT) + value
    
    def update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def add_task_item(self, task):
        """Add a task item widget"""
        # Time stamp and task message
        task_layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(SIZE.TASK_ITEM_HEIGHT),
        )
        
        time_label = Label(
            text=task.get_time_str(),
            size_hint=(1, None),
            height=dp(SIZE.TIME_LABEL_HEIGHT),
            halign="left",
            font_size=dp(SIZE.DEFAULT_FONT),
            bold=True,
            color=COL.TEXT,
            padding=[dp(SPACE.FIELD_PADDING_X), 0, dp(SPACE.FIELD_PADDING_X), 0]
        )
        time_label.bind(size=time_label.setter("text_size"))
        
        task_message_label = Label(
            text=task.message,
            size_hint=(1, None),
            height=dp(SIZE.MESSAGE_LABEL_HEIGHT),
            halign="left",
            valign="top",
            font_size=dp(SIZE.DEFAULT_FONT),
            color=COL.TEXT,
            padding=[dp(SPACE.FIELD_PADDING_X), dp(0)]
        )
        
        def update_text_size(instance, value):
            width = value[0]
            instance.text_size = (width, None)
            
            def adjust_height(dt):
                needed_height = max(dp(SIZE.MESSAGE_LABEL_HEIGHT), instance.texture_size[1])
                instance.height = needed_height
                
                task_layout.height = time_label.height + instance.height
            
            # Schedule the height adjustment for next frame
            Clock.schedule_once(adjust_height, 0)
        
        task_message_label.bind(size=update_text_size)
        
        task_layout.add_widget(time_label)
        task_layout.add_widget(task_message_label)
        self.tasks_container.add_widget(task_layout)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_manager = TaskManager()
        self.root_layout = FloatLayout()
        self.layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"top": 1, "center_x": 0.5}
        )
        
        # Top bar with + button
        self.top_bar = TopBar(text="+")
        self.top_bar.bind(on_press=self.go_to_task_screen)
        self.layout.add_widget(self.top_bar)
        
        # Scrollable container for task groups
        self.scroll_container = ScrollContainer()
        
        # Bottom bar with ^ button
        self.bottom_bar = BottomBar(text="^")
        self.bottom_bar.bind(on_press=self.scroll_container.scroll_to_top)
        
        # Connect the bottom bar to the scroll container
        self.scroll_container.set_bottom_bar(self.bottom_bar)
        
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.root_layout.add_widget(self.bottom_bar)

        self.add_widget(self.root_layout)
    
    def go_to_task_screen(self, instance):
        self.manager.current = "task"
    
    def load_tasks(self):
        """Load and display tasks"""
        self.task_manager.load_tasks()
        self.update_task_display()
    
    def update_task_display(self):
        """Update the task display with current tasks"""
        self.scroll_container.clear_widgets()
        
        # Get tasks grouped by date
        task_groups = self.task_manager.get_tasks_by_date()
        
        if not task_groups:
            no_tasks_label = Label(
                text="No tasks yet. Add one by tapping the + button!",
                size_hint=(1, None),
                height=dp(SIZE.NO_TASKS_LABEL_HEIGHT),
                color=COL.TEXT
            )
            self.scroll_container.add_widget_to_container(no_tasks_label)
            return
        
        # Add task groups to display
        for group in task_groups:
            task_group = TaskGroup(
                date_str=group["date"],
                tasks=group["tasks"],
                size_hint=(1, None)  # Allow height to be calculated
            )
            self.scroll_container.add_widget_to_container(task_group)
    
    def on_enter(self):
        """Called when screen is entered"""
        # Update task display whenever we return to this screen
        self.update_task_display() 
    