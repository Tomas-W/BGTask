import time

from .home_widgets import (TimeContainer, TaskContainer,
                           TaskLabel, TimeLabel, TaskGroupWidget, AlarmTimeContainer)

from managers.tasks.task import Task
from src.utils.logger import logger


class HomeScreenUtils:
    def __init__(self):
        pass
    
    def _refresh_home_screen(self, *args) -> None:
        """Refreshes task_groups and rebuilds the HomeScreen UI."""
        start_time = time.time()
        self.task_manager.refresh_task_groups()
        self.scroll_container.container.clear_widgets()
        for task_group in self.task_manager.task_groups:
            task_group_widget = TaskGroupWidget(date_str=task_group.date_str,
                                          tasks=task_group.tasks,
                                          task_manager=self.task_manager,
                                          parent_screen=self,
                                          clickable=True)
            self.scroll_container.container.add_widget(task_group_widget)
        
        logger.info(f"Refreshing HomeScreen took: {round(time.time() - start_time, 6)} seconds")
    
    def get_task_group(self, task: Task) -> TaskGroupWidget | None:
        """Returns the TaskGroup widget that contains the Task."""
        task_id = task.task_id
        for task_group in self.scroll_container.container.children:
            # Find TaskGroupWidget
            if not isinstance(task_group, TaskGroupWidget):
                continue
            # Check if it contains the Task
            for task_item in task_group.tasks:
                if task_item.task_id == task_id:
                    return task_group
        return None

    def get_task_container(self, task_group: TaskGroupWidget, task: Task) -> TaskContainer | None:
        """Returns the TaskContainer that contains the Task."""
        task_id = task.task_id
        # Search through the TaskGroupWidget's children
        for task_container in task_group.task_group_container.children:
            if not isinstance(task_container, TaskContainer):
                continue
            # Check each child for TaskLabel
            for child in task_container.children:
                if isinstance(child, TaskLabel) and getattr(child, "task_id", None) == str(task_id):
                    # Find TimeLabel
                    for sibling in task_container.children:
                        if isinstance(sibling, TimeContainer):
                            for time_component in sibling.children:
                                if isinstance(time_component, AlarmTimeContainer):
                                    for time_label in time_component.children:
                                        if isinstance(time_label, TimeLabel):
                                            # Save TimeLabel
                                            self.time_label_widget = time_label
                                            break
                    return task_container
        return None

    def get_task_message_widget(self, task_container: TaskContainer) -> TaskLabel:
        """Returns the TaskLabel widget from a TaskContainer."""
        for child in task_container.children:
            if isinstance(child, TaskLabel):
                self.task_message_widget = child
                return child
        return None
    
    def clear_go_to_task_references(self) -> None:
        """Clears the go to widget attributes."""
        self.task_header_widget = None
        self.time_label_widget = None
        self.task_message_widget = None
