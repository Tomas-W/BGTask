from typing import Any, Optional, Dict, List, Tuple

from jnius import autoclass  # type: ignore


class PreferencesManager:
    """
    Manages SharedPreferences for both App and Service contexts.
    - ServicePreferencesManager provides context
    - AppPreferencesManager gets it from PythonActivity.mActivity
    """
    def __init__(self, service_context: Optional[Any] = None):
        self.context, self.Context = self._initialize_context(service_context)
        
    def _initialize_context(self, service_context: Optional[Any]) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Initializes and returns the context and Context class.
        Returns (None, None) if context cannot be obtained.
        """
        try:
            # If Service, get its context and return
            if service_context is not None:
                Context = autoclass("android.content.Context")
                return service_context, Context

            # If App, get context from PythonActivity.mActivity
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            
            if not hasattr(PythonActivity, "mActivity"):
                print("     Error: PythonActivity.mActivity not available")
                return None, None

            context = PythonActivity.mActivity.getApplicationContext()
            return context, Context

        except Exception as e:
            print(f"     Error initializing SharedPreferences context: {e}")
            return None, None

    def _is_context_valid(self) -> bool:
        """Returns True if context is valid, False otherwise."""
        if not self.context or not self.Context:
            print("     Error: No valid context available")
            return False
        return True

    def set_preferences(self, pref_type: str, extras: Dict[str, Any]) -> None:
        """
        Stores values in SharedPreferences under the given pref_type.
        Uses the context initialized in __init__.
        """
        if not self._is_context_valid():
            return

        try:
            prefs = self.context.getSharedPreferences(pref_type, self.Context.MODE_PRIVATE)
            editor = prefs.edit()

            for key, value in extras.items():
                editor.putString(key, str(value))
            
            editor.commit()
            print(f"     Stored SharedPreferences in {pref_type}: {extras}")

        except Exception as e:
            print(f"     Error storing SharedPreferences: {e}")

    def get_preferences(self, pref_type: str, keys: List[str]) -> Dict[str, Optional[str]]:
        """
        Returns a dictionary of the requested keys from SharedPreferences.
        Value is set to None if not found.
        Uses the context initialized in __init__.
        """
        result = {}
        
        if not self._is_context_valid():
            return result
        
        try:
            prefs = self.context.getSharedPreferences(pref_type, self.Context.MODE_PRIVATE)
            
            for key in keys:
                value = prefs.getString(key, None)
                result[key] = value
            
            print(f"Read SharedPreferences from {pref_type}: {result}")
            return result

        except Exception as e:
            print(f"Error reading SharedPreferences: {e}")
            return result

    def get_and_delete_preference(self, pref_type: str, key: str) -> Optional[str]:
        """
        Returns the value of the key and deletes it from SharedPreferences.
        Returns None if the key is not found.
        Uses the context initialized in __init__.
        """
        if not self._is_context_valid():
            return None
        
        try:
            prefs = self.context.getSharedPreferences(pref_type, self.Context.MODE_PRIVATE)
            value = prefs.getString(key, None)
            
            if value is not None:
                editor = prefs.edit()
                editor.remove(key)
                editor.commit()
                print(f"Read and deleted SharedPreferences from {pref_type}: {key}={value}")
                
            return value

        except Exception as e:
            print(f"Error reading/deleting SharedPreferences: {e}")
            return None
