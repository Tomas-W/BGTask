[app]
title = BGTask
package.name = bgtask
package.domain = org.bgtask

source.dir = .

source.include_exts = py,png,json,wav,db
source.exclude_exts = gitignore,md,db-shm,db-wal
source.exclude_dirs = bin,.venv,__pycache__,.buildozer,.buildozer.venv

requirements = kivy,pillow,android.storage,jnius,plyer,loguru,sqlite3

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

android.archs = arm64-v8a
