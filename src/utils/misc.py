from managers.device.device_manager import DM


def is_widget_visible(widget, scroll_view):
    if not widget or not scroll_view:
        return False
    
    # Get ScrollView viewport size and position
    view_y = scroll_view.y
    view_height = scroll_view.height
    view_bottom = view_y
    view_top = view_y + view_height
    
    # Get widget position relative to ScrollView
    widget_y = widget.to_window(*widget.pos)[1] - scroll_view.to_window(0, 0)[1]
    widget_height = widget.height
    widget_bottom = widget_y
    widget_top = widget_y + widget_height
    
    # Check if widget is fully visible in viewport
    return widget_bottom >= view_bottom and widget_top <= view_top
