from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp

from src.utils.taskmanager import TaskManager
from src.screens.home.task_group import TaskGroup

from src.utils.widgets import TopBar, BottomBar, ScrollContainer
from src.settings import COL, SIZE


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
        self.scroll_container.connect_bottom_bar(self.bottom_bar)
        
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.root_layout.add_widget(self.bottom_bar)
        self.add_widget(self.root_layout)
    
    def go_to_task_screen(self, instance):
        self.manager.current = "task"
    
    def load_tasks(self):
        self.task_manager.load_tasks()
        self.update_task_display()
    
    def update_task_display(self):
        self.scroll_container.clear_widgets()
        
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
                size_hint=(1, None)
            )
            self.scroll_container.add_widget_to_container(task_group)
    
    def on_enter(self):
        """Called when screen is entered"""
        self.update_task_display() 
    