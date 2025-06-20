import functools

from managers.device.device_manager import DM
from src.utils.timer import TIMER
from src.utils.logger import logger


def log_time(name):
    """
    Decorator to log duration of a method or function.
    Usage: @log_time("name_to_time")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            TIMER.start(name)
            result = func(self, *args, **kwargs)
            TIMER.stop(name)
            
            logger.timing(f"Loading {name} took: {TIMER.get_time(name)}")
            return result
        return wrapper
    return decorator


def android_only(func):
    """
    Function decorator that returns early if the device is not Android.
    Logs class name for class methods and function name for regular functions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        
        if args and hasattr(args[0], "__class__"):
            # Get class name
            class_name = args[0].__class__.__name__
            if not DM.is_android:
                logger.debug(f"Device is not android, skipping {class_name}.{func_name}")
                return
        else:
            # Get module name
            module_name = func.__module__.split(".")[-1]
            if not DM.is_android:
                logger.debug(f"Device is not android, skipping {module_name}.{func_name}")
                return
                
        return func(*args, **kwargs)
    return wrapper


def android_only_class(except_methods=None):
    """
    Class decorator that applies android_only to all methods in the class.
    - except_methods: List of method names that should not be decorated.
    """
    if except_methods is None:
        except_methods = []
        
    def decorator(cls):
        for name, method in cls.__dict__.items():
            if (callable(method) and 
                name not in except_methods):
                setattr(cls, name, android_only(method))
        return cls
    return decorator


def disable_gc(func):
    """
    Decorator that disables garbage collection during function execution.
    Re-enables GC after function completes and schedules a light cleanup.
    """
    import gc
    from kivy.clock import Clock
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        gc.disable()
        
        try:
            result = func(*args, **kwargs)
            return result
            
        finally:
            gc.enable()
            # Light cleanup
            gc.collect(0)
    
    return wrapper
