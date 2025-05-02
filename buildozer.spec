[app]
title = BGTask
package.name = bgtask
package.domain = org.bgtask

source.dir = .

source.include_exts = py,png,json,wav
source.exclude_exts = gitignore,md
source.exclude_dirs = bin,.venv,__pycache__,.buildozer,.buildozer.venv

requirements = kivy,pillow,jnius,plyer,loguru,android

# Include the service directory
source.include_patterns = service/*

source.assets = assets/

version = 0.1

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,SET_WALLPAPER,VIBRATE,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,POST_NOTIFICATIONS

services = BGTaskService:service/main.py:foreground:sticky

android.entrypoint = org.kivy.android.PythonActivity

android.activity_launch_mode = singleTask

android.wakelock = True

android.api = 33
android.minapi = 21
android.ndk = 25b

# Python optimization settings
android.optimize_python = True
android.precompile_python = True
android.allow_backup = 0

android.archs = arm64-v8a

android.gradle_dependencies = androidx.core:core:1.6.0
android.enable_androidx = True
