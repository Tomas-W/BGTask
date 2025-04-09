import time

from functools import lru_cache
from typing import TYPE_CHECKING

from src.utils.logger import logger
from .home_widgets import (TasksByDate, TimeContainer, EditTaskButton,
                           EditTaskButtonContainer, TaskContainer, TaskLabel,
                           TimeLabel)

if TYPE_CHECKING:
    from src.managers.tasks.task_manager_utils import Task


class HomeScreenUtils:
    def __init__(self):
        pass

    def update_task_display(self, *args) -> None:
        """
        Update the Task widgets, reusing cached widgets when possible
        """
        start_time = time.time()
        self.scroll_container.container.clear_widgets()
        self.edit_delete_buttons = []
        
        # On Task update, invalidate the cache for that date
        if hasattr(self, "invalidate_cache_for_date") and self.invalidate_cache_for_date:
            date_to_invalidate = self.invalidate_cache_for_date
            keys_to_remove = [k for k in self.widget_cache if k.startswith(f"{date_to_invalidate}:")]
            for key in keys_to_remove:
                del self.widget_cache[key]
            self.invalidate_cache_for_date = None
        
        # Keep track of which can be removed from cache
        used_cache_keys = set()
        self.tasks_by_dates = []
        
        task_groups = self.task_manager.get_sorted_tasks()
        all_expired_states = {}
        for group in task_groups:
            tasks = group["tasks"]
            if tasks:
                date_str = group["date"]
                all_expired = all(task.expired for task in tasks)
                all_expired_states[date_str] = all_expired
        
        for group in task_groups:
            date_str = group["date"]
            tasks = group["tasks"]
            
            if not tasks:
                continue
            
            # Create cache key
            time_and_message_parts = []
            for task in sorted(tasks, key=lambda t: t.timestamp):
                # Include timestamp and message hash
                msg_hash = str(hash(task.message))[:8]
                time_and_message_parts.append(f"{task.timestamp.isoformat()}:{msg_hash}")
            
            cache_key = f"{date_str}:{','.join(time_and_message_parts)}"
            
            if cache_key in self.widget_cache:
                # Reuse cache
                task_group = self.widget_cache[cache_key]
                
                # Update expired status
                all_expired = all_expired_states.get(date_str, False)
                if task_group.all_expired != all_expired:
                    task_group.tasks_container.set_expired(all_expired)
                    task_group.all_expired = all_expired
            else:
                # Create new widget
                task_group = TasksByDate(
                    date_str=date_str,
                    tasks=tasks,
                    task_manager=self.task_manager,
                    parent_screen=self,
                    size_hint=(1, None)
                )
                task_group.all_expired = all_expired_states.get(date_str, False)
                self.widget_cache[cache_key] = task_group
                
            # Add to container - add_widget is expensive, only do it once per group
            self.scroll_container.container.add_widget(task_group)
            self.tasks_by_dates.append(task_group)
            used_cache_keys.add(cache_key)
            
            # Collect edit/delete buttons efficiently
            self._collect_edit_buttons(task_group)
        
        # Clean up unused cache
        self.widget_cache = {k: v for k, v in self.widget_cache.items() if k in used_cache_keys}
        # Compensate for BottomBar
        self.check_bottom_bar_state()
        # Update edit/delete button visibility
        self.check_for_edit_delete()
        
        self.tasks_loaded = True
        end_time = time.time()
        logger.error(f"HomeScreenUtils update_task_display time: {end_time - start_time}")
    
    def _collect_edit_buttons(self, task_group: TasksByDate) -> None:
        """Helper method to collect edit buttons from a Task group"""
        for task_container in task_group.tasks_container.children:
            for child in task_container.children:
                if isinstance(child, TimeContainer):
                    for component in child.children:
                        if isinstance(component, EditTaskButtonContainer):
                            buttons = [b for b in component.children if isinstance(b, EditTaskButton)]
                            if buttons:
                                self.edit_delete_buttons.extend(buttons)

    @lru_cache(maxsize=32)
    def get_task_group(self, task: "Task") -> TasksByDate:
        """Get the TaskGroup that contains the Task"""
        task_id = task.task_id
        for task_group in self.tasks_by_dates:
            for t in task_group.tasks:
                if t.task_id == task_id:
                    return task_group
        return None
    
    @lru_cache(maxsize=32)
    def get_task_container(self, task_group: TasksByDate, task: "Task") -> TaskContainer:
        """Get the TaskContainer that contains the Task"""
        task_time = task.get_time_str()
        task_id = task.task_id
        for task_container in task_group.tasks_container.children:
            if getattr(task_container, "task_id", None) == task_id:
                return task_container
                
            for child in task_container.children:
                if isinstance(child, TimeContainer):
                    for time_component in child.children:
                        if isinstance(time_component, TimeLabel) and time_component.text == task_time:
                            self.time_label_widget = time_component
                            return task_container
        return None

    @lru_cache(maxsize=32)
    def get_task_message_widget(self, task_container: TaskContainer) -> TaskLabel:
        """Get the TaskLabel that contains the Task message"""
        for child in task_container.children:
            if isinstance(child, TaskLabel):
                self.task_message_widget = child
                return child
        return None
    
    def clear_go_to_task_references(self) -> None:
        """Clear the go to widget attributes"""
        self.task_header_widget = None
        self.time_label_widget = None
        self.task_message_widget = None
        
        # Clear caches
        self.get_task_group.cache_clear()
        self.get_task_container.cache_clear()
        self.get_task_message_widget.cache_clear()
    
    def register_edit_delete_button(self, button: EditTaskButton) -> None:
        """Register an edit/delete button with this screen"""
        self.edit_delete_buttons.append(button)
