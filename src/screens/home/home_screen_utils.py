from src.utils.logger import logger
from .home_widgets import (TasksByDate, TimeContainer, EditTaskButton,
                           EditTaskButtonContainer, TaskContainer, TaskLabel,
                           TimeLabel)



class HomeScreenUtils:
    def __init__(self):
        pass

    def update_task_display(self, *args) -> None:
        """
        Update the Task widgets, reusing cached widgets when possible
        """
        # Clear container but don't discard widgets yet
        self.scroll_container.container.clear_widgets()
        self.edit_delete_buttons = []
        
        # When a task is updated, we should invalidate the cache for that date
        # to ensure we rebuild the affected widgets
        if hasattr(self, "invalidate_cache_for_date") and self.invalidate_cache_for_date:
            # Remove any cache entries that contain the date we need to refresh
            keys_to_remove = [k for k in self.widget_cache.keys() 
                             if self.invalidate_cache_for_date in k.split(":")[0]]
            for key in keys_to_remove:
                del self.widget_cache[key]
            self.invalidate_cache_for_date = None
        
        # Keep track of used widgets to identify which can be removed from cache
        used_cache_keys = set()
        self.tasks_by_dates = []
        
        # Process task groups
        for group in self.task_manager.get_tasks_by_dates():
            date_str = group["date"]
            tasks = group["tasks"]
            
            # Create cache key based on date and task IDs + content hash
            # Include message content in cache key to detect changes
            task_keys = [f"{task.task_id}:{hash(task.message)}:{task.timestamp.isoformat()}:{task.alarm_name}:{task.vibrate}" 
                         for task in tasks]
            task_keys.sort()  # Sort for consistency
            cache_key = f"{date_str}:{','.join(task_keys)}"
            
            if cache_key in self.widget_cache:
                # Reuse cached widget
                task_group = self.widget_cache[cache_key]
                # Update expired status if needed
                if tasks and all(task.expired for task in tasks):
                    task_group.tasks_container.set_expired(True)
                    task_group.all_expired = True
                else:
                    task_group.tasks_container.set_expired(False)
                    task_group.all_expired = False
            else:
                # Create new widget
                task_group = TasksByDate(
                    date_str=date_str,
                    tasks=tasks,
                    task_manager=self.task_manager,
                    parent_screen=self,
                    size_hint=(1, None)
                )
                # Add to cache
                self.widget_cache[cache_key] = task_group
                
            # Add to container
            self.scroll_container.container.add_widget(task_group)
            self.tasks_by_dates.append(task_group)
            used_cache_keys.add(cache_key)
            
            # Re-register edit/delete buttons
            for task_container in task_group.tasks_container.children:
                for child in task_container.children:
                    if isinstance(child, TimeContainer):
                        for component in child.children:
                            if isinstance(component, EditTaskButtonContainer):
                                for button in component.children:
                                    if isinstance(button, EditTaskButton):
                                        self.edit_delete_buttons.append(button)
        
        # Clean up unused cached widgets
        keys_to_remove = [k for k in self.widget_cache.keys() if k not in used_cache_keys]
        for key in keys_to_remove:
            del self.widget_cache[key]
        
        # Compensate for BottomBar
        self.check_bottom_bar_state()
        
        # Update edit/delete button visibility
        self.check_for_edit_delete()
        logger.debug(f"Updated task display with {len(used_cache_keys)} cached widgets")
    
    def get_task_group(self, task) -> TasksByDate:
        """Get the TaskGroup that contains the task"""
        for task_group in self.tasks_by_dates:
            if task in task_group.tasks:
                return task_group
        return None
    
    def get_task_container(self, task_group, task) -> TaskContainer:
        """Get the TaskContainer that contains the task"""
        task_time = task.get_time_str()
        for task_container in task_group.tasks_container.children:
            for child in task_container.children:

                if isinstance(child, TimeContainer):
                    for time_component in child.children:
                        # Confirm time entry & save the Task's container
                        if isinstance(time_component, TimeLabel):
                            if time_component.text == task_time:
                                self.time_label_widget = time_component
                                logger.error(f"Time label widget: {self.time_label_widget}")
                                return task_container
        return None

    def get_task_message_widget(self, task_container) -> TaskLabel:
        """Get the TaskLabel that contains the task message"""
        for child in task_container.children:
            if isinstance(child, TaskLabel):
                self.task_message_widget = child
                logger.error(f"Task message widget: {self.task_message_widget}")
                return child
        return None
    
    def clear_go_to_task_references(self):
        """Clear the go to widget attributes"""
        self.task_header_widget = None
        self.time_label_widget = None
        self.task_message_widget = None
    
    def register_edit_delete_button(self, button: "EditTaskButton") -> None:
        """Register an edit/delete button with this screen"""
        self.edit_delete_buttons.append(button)
    
