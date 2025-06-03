import time
from datetime import datetime

from functools import lru_cache
from typing import TYPE_CHECKING

from src.utils.logger import logger
from .home_widgets import (TasksByDate, TimeContainer, TaskContainer,
                           TaskLabel, TimeLabel)

if TYPE_CHECKING:
    from managers.tasks.task import Task


class HomeScreenUtils:
    def __init__(self):
        pass

    def update_task_display(self, *args, modified_task=None) -> None:
        """
        Update the Task widgets, reusing cached widgets when possible
        
        Args:
            modified_task: If provided, invalidate cache for this task's date
        """
        logger.debug("UPDATE TASK DISPLAY")
        logger.trace(f"Modified task: {modified_task.message if modified_task else None}")
        start_time = time.time()
        
        # Step 1: Clear container but don't discard widgets yet
        self.scroll_container.container.clear_widgets()
        
        # Step 2: If we have a modified task, invalidate cache for its date
        if modified_task:
            modified_date = modified_task.get_date_str()
            self._invalidate_cache_for_date(modified_date)
            logger.debug(f"Invalidated cache for date: {modified_date}")
        
        # Keep track of used widgets to identify which can be removed from cache
        used_cache_keys = set()
        self.active_task_widgets = []
        
        # Step 3: Get updated task data
        self.task_manager.sort_active_tasks()
        task_groups = self.task_manager.sorted_active_tasks
        
        # Step 4: Process each task group
        for group in task_groups:
            if not group["tasks"]:
                continue
                
            date_str = group["date"]
            tasks = group["tasks"]
            
            # Create a cache key for this group
            cache_key = self._make_cache_key(date_str, tasks)
            
            # Try to get from cache or create new
            task_group = self._create_task_group(group)
            
            # Add to container and tracking list
            self.scroll_container.container.add_widget(task_group)
            self.active_task_widgets.append(task_group)
            used_cache_keys.add(cache_key)
        
        # Step 5: Clean up unused cached widgets
        self.widget_cache = {k: v for k, v in self.widget_cache.items() if k in used_cache_keys}
        
        # Restore selected task if needed
        has_selected_task = hasattr(self, "selected_task") and self.selected_task
        if has_selected_task:
            is_deletion = modified_task and not self.task_manager.get_task_by_id(str(modified_task.task_id))
            if not is_deletion:
                self._restore_task_selection(self.selected_task.task_id)
        
        # Update UI state
        self.check_bottom_bar_state()
        
        self.tasks_loaded = True
        end_time = time.time()
        logger.error(f"HomeScreenUtils update_task_display time: {end_time - start_time:.4f}s")
    
    def _invalidate_cache_for_date(self, date_str):
        """Remove all cached widgets for a specific date"""
        keys_to_remove = [k for k in self.widget_cache if k.startswith(f"{date_str}:")]
        for key in keys_to_remove:
            del self.widget_cache[key]
    
    def _resort_task_groups(self):
        """Resort task groups and rebuild the container in sorted order"""
        # Sort by timestamp of first task in each group
        self.active_task_widgets.sort(
            key=lambda x: x.tasks[0].timestamp if x.tasks else datetime.max
        )
        
        # Rebuild container in sorted order
        self.scroll_container.container.clear_widgets()
        for group in self.active_task_widgets:
            self.scroll_container.container.add_widget(group)

    def _restore_task_selection(self, task_id):
        """Restore task selection after UI update"""
        if not task_id or not hasattr(self, "selected_task") or not hasattr(self, "select_task"):
            return
            
        # Convert to string to ensure consistency
        task_id = str(task_id)
            
        # Find the task in updated UI
        task = self.task_manager.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found in _restore_task_selection")
            # Clear selection state since task doesn't exist anymore
            self.selected_task = None
            self.selected_label = None
            if hasattr(self, "hide_floating_buttons"):
                self.hide_floating_buttons()
            return
            
        # Find the TaskLabel for this task
        found = False
        for task_group in self.active_task_widgets:
            for task_container in task_group.tasks_container.children:
                for child in task_container.children:
                    # Check if it's a TaskLabel with our task
                    if hasattr(child, "task_id") and child.task_id and str(child.task_id) == task_id:
                        # Re-select this task
                        self.selected_task = task  # Use the fresh task from task_manager
                        self.selected_label = child
                        child.set_selected(True)
                        found = True
                        return
        
        # If we get here, we didn't find the task in the UI
        if not found:
            self.selected_task = None
            self.selected_label = None
            if hasattr(self, "hide_floating_buttons"):
                self.hide_floating_buttons()

    def _full_rebuild_task_display(self) -> None:
        """
        Initial build of the task display when app is launched / resumed.
        Creates all task widgets and caches them for future use.
        """
        start_time = time.time()
        self.scroll_container.container.clear_widgets()
        self.active_task_widgets = []
        
        # Get sorted tasks
        self.task_manager.sort_active_tasks()
        task_groups = self.task_manager.sorted_active_tasks
        
        if not task_groups:
            self.tasks_loaded = True
            return
        
        nr_tasks = 0
        for group in task_groups:
            if not group["tasks"]:
                continue
            nr_tasks += len(group["tasks"])  # Count tasks for logging
            # Create new task group widget
            date_str = group["date"]
            tasks = group["tasks"]
            
            task_group = TasksByDate(
                date_str=date_str,
                tasks=tasks,
                task_manager=self.task_manager,
                parent_screen=self,
                size_hint=(1, None)
            )
            
            # Add to container
            self.scroll_container.container.add_widget(task_group)
            self.active_task_widgets.append(task_group)
                        
            # Cache the widget for future use
            cache_key = self._make_cache_key(date_str, tasks)
            self.widget_cache[cache_key] = task_group

        self.tasks_loaded = True
        end_time = time.time()
        logger.error(f"HomeScreenUtils _full_rebuild_task_display time: {end_time - start_time}")
        logger.debug(f"Loaded {len(task_groups)} task groups with {nr_tasks} tasks")
    
    def _create_task_group(self, group, all_expired_states=None) -> TasksByDate:
        """Create a TasksByDate widget for a group of tasks"""
        date_str = group["date"]
        tasks = group["tasks"]
        
        # Create cache key
        cache_key = self._make_cache_key(date_str, tasks)
        
        # Check if we need to calculate expired state
        if all_expired_states is None:
            all_expired = all(task.expired for task in tasks)
        else:
            all_expired = all_expired_states.get(date_str, False)
            
        if cache_key in self.widget_cache:
            # Reuse cache
            task_group = self.widget_cache[cache_key]
            
            # Update expired status
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
            task_group.all_expired = all_expired
            self.widget_cache[cache_key] = task_group
            
        return task_group
    
    def _make_cache_key(self, date_str, tasks) -> str:
        """Create a cache key for a group of tasks"""
        time_and_message_parts = []
        for task in sorted(tasks, key=lambda t: t.timestamp):
            # Include timestamp and message hash
            msg_hash = str(hash(task.message))[:8]
            time_and_message_parts.append(f"{task.timestamp.isoformat()}:{msg_hash}")
        
        return f"{date_str}:{','.join(time_and_message_parts)}"
    
    @lru_cache(maxsize=32)
    def get_task_group(self, task: "Task") -> TasksByDate:
        """Get the TaskGroup that contains the Task"""
        task_id = task.task_id
        for task_group in self.active_task_widgets:
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
