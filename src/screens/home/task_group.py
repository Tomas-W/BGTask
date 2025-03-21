from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from src.utils.containers import TaskContainer, TaskBox
from src.utils.labels import TaskHeader, TimeLabel, TaskLabel

from src.settings import SPACE, SIZE


class TaskGroup(BoxLayout):
    """
    Displays tasks grouped by date.
    Day header on top, tasks below with blue bg.
    """
    def __init__(self, date_str, tasks, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        # Header with day name and int
        day_header = TaskHeader(text=date_str)
        self.add_widget(day_header)
        
        # Tasks container
        self.tasks_container = TaskBox()
        for task in tasks:
            self.add_task_item(task)
        self.add_widget(self.tasks_container)
        
        self.height = day_header.height + self.tasks_container.height
        self.tasks_container.bind(height=self.update_group_height)
    
    def update_group_height(self, instance, value):
        """Update the overall height when tasks_container height changes"""
        self.height = dp(SPACE.SPACE_XS) + dp(SIZE.HEADER_HEIGHT) + value
    
    def add_task_item(self, task):
        """Add a task item widget"""
        # Time stamp and task message
        task_container = TaskContainer()
        time_label = TimeLabel(text=task.get_time_str())
        task_label = TaskLabel(text=task.message)
        
        def update_text_size(instance, value):
            width = value[0]
            instance.text_size = (width, None)
            
            def adjust_height(dt):
                needed_height = max(dp(SIZE.MESSAGE_LABEL_HEIGHT), instance.texture_size[1])
                instance.height = needed_height
                
                task_container.height = time_label.height + instance.height
            
            # Schedule the height adjustment for next frame
            Clock.schedule_once(adjust_height, 0)
        
        task_label.bind(size=update_text_size)
        
        task_container.add_widget(time_label)
        task_container.add_widget(task_label)
        self.tasks_container.add_widget(task_container)
        