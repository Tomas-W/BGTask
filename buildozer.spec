[app]
title = BGTask
package.name = bgtask
package.domain = org.bgtask

source.dir = .

source.include_exts = py,png,json,wav
source.exclude_exts = gitignore,md
source.exclude_dirs = bin,.venv,__pycache__,.buildozer,.buildozer.venv

requirements = kivy,pillow,android.storage,jnius,plyer,loguru

source.assets = assets/

version = 0.1

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,SET_WALLPAPER
android.api = 33
android.minapi = 21
android.ndk = 25b

android.optimize_python = True
android.precompile_python = True
android.use_legacy_android_support = 0
android.allow_backup = 0

android.archs = arm64-v8a
