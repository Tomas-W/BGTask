import os
import pstats
import re
import shutil
import time


class ProfileAnalyzer:
    def __init__(self):
        self.base_dir = os.path.join(os.getcwd(), "profiler")
        self.profile_path = os.path.join(self.base_dir, "data", "myapp.profile")
        self.raw_data_file = os.path.join(self.base_dir, "data", "raw_data.txt")
        self.profile_data = None

        self.datestamp = time.strftime("%A %d @ %H:%M")
    
    def _load_data(self):
        if self.profile_data is not None:
            return

        with open(self.raw_data_file, "w") as f:
            stats = pstats.Stats(self.profile_path, stream=f)
            stats.strip_dirs().sort_stats("time").print_stats()
        
        self.profile_data = []
        with open(self.raw_data_file, "r") as file:
            for line in file:
                parts = re.split(r'\s{2,}', line.strip())
                if not len(parts) == 5 or not parts[0][0].isdigit():
                    continue
                
                n_calls = parts[0].split("/")[-1]
                func_name = re.sub(r'^\d+\.?\d*\s+', '', parts[-1])
                
                self.profile_data.append({
                    "n_calls": n_calls,
                    "total_time": float(parts[1]),
                    "percall_time": float(parts[2].split()[0]),
                    "cum_time": float(parts[3].split()[0]),
                    "func_name": func_name
                })
    
    def _write_report(self, filename, title, time_key):
        self._load_data()
        
        sorted_data = sorted(
            self.profile_data,
            key=lambda x: x[time_key],
            reverse=True
        )
        
        output_path = os.path.join(self.base_dir, filename)
        with open(output_path, "w") as f:
            f.write(f"{title}  -  {self.datestamp}\n\n")
            f.write("  calls      time  function\n")
            
            for entry in sorted_data:
                time_str = f"{entry[time_key]:.4f}"
                f.write(f"{entry['n_calls']:>7}  {time_str:>8}  {entry['func_name']}\n")
    
    def get_total(self):
        self._write_report("total_time.txt", "Total time", "total_time")
    
    def get_percall(self):
        self._write_report("percall_time.txt", "Per call time", "percall_time")
    
    def get_cumulative(self):
        self._write_report("cum_time.txt", "Cumulative time", "cum_time")
    
    def get_all(self):
        self.get_total()
        self.get_percall()
        self.get_cumulative()

    def copy_profile_to_shared(self):
        try:
            from android.storage import primary_external_storage_path  # type: ignore
            from jnius import autoclass  # type: ignore
            
            # Get the Documents directory on external storage
            ext_path = primary_external_storage_path()
            dest_dir = os.path.join(ext_path, "Documents", "BGTask")
            
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            dest_file = os.path.join(dest_dir, f"profile_{self.datestamp.replace(':', '-').replace(' ', '_')}.profile")
            shutil.copy2(self.profile_path, dest_file)
            
            MediaScannerConnection = autoclass("android.media.MediaScannerConnection")
            Context = autoclass("android.content.Context")
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            MediaScannerConnection.scanFile(activity, [dest_file], None, None)
            
            return dest_file
            
        except ImportError:
            return "Not running on Android"
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    analyzer = ProfileAnalyzer()
    analyzer.get_all()

if __name__ == "__main__":
    main()
