[app]
title = BGTask
package.name = bgtask
package.domain = org.bgtask

source.dir = .

source.include_exts = py,png,json,wav
source.exclude_exts = gitignore,md
source.exclude_dirs = bin,.venv,__pycache__,.buildozer,.buildozer.venv

requirements = kivy,pillow,android.storage,jnius,plyer,loguru

# Include the service directory
source.include_patterns = service/*

source.assets = assets/

version = 0.1

orientation = portrait
fullscreen = 0

# Add all required permissions for background service
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,SET_WALLPAPER,VIBRATE,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE_SPECIAL_USE


# Specify the main activity class
android.entrypoint = org.kivy.android.PythonActivity

# Add custom meta-data to AndroidManifest.xml
android.meta_data = android.allow_multiple_resumed_activities=true,android.allow_task_reparenting=true

# Force single task mode
android.activity_launch_mode = singleTask

# Keep the app in memory
android.wakelock = True

android.api = 33
android.minapi = 21
android.ndk = 25b

android.optimize_python = True
android.precompile_python = True
android.use_legacy_android_support = 0
android.allow_backup = 0

android.archs = arm64-v8a
