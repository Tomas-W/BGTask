from functools import wraps
from typing import Callable, TypeVar, ParamSpec

from managers.device.device_manager import DM
from src.utils.logger import logger
from src.utils.timer import TIMER


def log_time(name):
    """
    Decorator to log duration of a method or function.
    Usage: @log_time("name_to_time")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            TIMER.start(name)
            result = func(self, *args, **kwargs)
            TIMER.stop(name)
            
            return result
        return wrapper
    return decorator


def android_only(func):
    """
    Function decorator that returns early if the device is not Android.
    Logs class name for class methods and function name for regular functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DM.is_android:
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


T = TypeVar("T")
P = ParamSpec("P")
def requires_gps(func: Callable[P, T]) -> Callable[P, T | None]:
    """
    Decorator that ensures GPS is initialized before executing GPS-dependent functions.
    If GPS is not initialized, try to initialize it.
    Returns None and shows a popup if GPS initialization fails.
    """
    @wraps(func)
    def wrapper(self: "ServiceGpsManager", *args: P.args, **kwargs: P.kwargs) -> T | None: # type: ignore
        if not self._ensure_gps_initialized():
            logger.warning(f"GPS not initialized, cannot execute {func.__name__}")
            return None
        return func(self, *args, **kwargs)
    return wrapper


def disable_gc(func):
    """
    Decorator that disables garbage collection during function execution.
    Re-enables GC immediately after function completes and schedules small collection.
    """
    import gc
    from kivy.clock import Clock
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        gc.disable()
        
        try:
            return func(*args, **kwargs)
        
        finally:
            gc.enable()
            Clock.schedule_once(lambda dt: gc.collect(0), 0)
    
    return wrapper
