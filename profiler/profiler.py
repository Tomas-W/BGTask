import cProfile
import os
import shutil
import time

from typing import Optional

from managers.device.device_manager import DM
from src.utils.wrappers import android_only


class Profiler:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    PROFILER_DIR = os.path.join(PROJECT_ROOT, "profiler")
    PROFILE_FILENAME = "BGTask.profile"
    
    # Java class strings
    MEDIA_SCANNER = "android.media.MediaScannerConnection"
    PYTHON_ACTIVITY = "org.kivy.android.PythonActivity"
    
    def __init__(self):
        self.profile: Optional[cProfile.Profile] = None
        self.profile_path: Optional[str] = None
        
    def start(self) -> None:
        """Start profiling the application."""
        self.profile = cProfile.Profile()
        self.profile.enable()
        
    def stop(self) -> None:
        """Stop profiling and save the results."""
        if not self.profile:
            raise RuntimeError("Profiler was not started")
            
        self.profile.disable()
        
        # Ensure profiler directory exists
        os.makedirs(self.PROFILER_DIR, exist_ok=True)
        
        # Save profile data
        self.profile_path = os.path.join(self.PROFILER_DIR, self.PROFILE_FILENAME)
        self.profile.dump_stats(self.profile_path)
        
        # Export to Android
        self._export_to_android()
    
    @android_only
    def _export_to_android(self) -> None:
        """Export profile data to Android external storage."""
        try:
            from android.storage import primary_external_storage_path  # type: ignore
            from jnius import autoclass  # type: ignore
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            ext_path = primary_external_storage_path()
            
            # Create BGTask/profiler directory on Android external storage
            android_profiler_dir = os.path.join(ext_path, "BGTask", "profiler")
            os.makedirs(android_profiler_dir, exist_ok=True)
            
            # Copy profile to Android with timestamp
            dest_file = os.path.join(android_profiler_dir, f"profile_{timestamp}.profile")
            shutil.copy2(self.profile_path, dest_file)
            
            # Notify Android media scanner using class variables
            MediaScannerConnection = autoclass(Profiler.MEDIA_SCANNER)
            activity = autoclass(Profiler.PYTHON_ACTIVITY).mActivity
            MediaScannerConnection.scanFile(activity, [dest_file], None, None)
            
            print(f"Profile exported to: {dest_file}")
            
        except Exception as e:
            print(f"Error exporting profile: {str(e)}")
            
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


profiler = Profiler()
