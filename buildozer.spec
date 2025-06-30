[app]
title = BGTask
package.name = bgtask
package.domain = org.bgtask
version = 0.1

# Source code and assets
source.dir = .
source.include_exts = 
    py,
    png,
    json,
    wav
source.exclude_exts = 
    gitignore,
    md
source.exclude_dirs = 
    bin,
    cache,
    .venv,
    __pycache__,
    .buildozer,
    .buildozer.venv
source.include_patterns = 
    service/*
source.assets = 
    assets/

# Requirements
requirements = 
    kivy,
    pillow,
    jnius,
    plyer,
    loguru,
    android,
    openssl,
    requests,
    urllib3,
    certifi,
    kivy_garden.mapview

# Android specific configurations
android.api = 33
android.minapi = 21
android.ndk = 25b
android.allow_backup = 0
android.archs = arm64-v8a, x86_64

# Display settings
orientation = portrait
fullscreen = 0

# Splash screen configuration
presplash.filename = presplash.png
android.presplash_color = #EDEDED

# Android resources
icon.filename = res/icon.png
android.add_resources = 
    res/drawable-mdpi/notification_icon.png:drawable-mdpi/notification_icon.png,
    res/drawable-hdpi/notification_icon.png:drawable-hdpi/notification_icon.png,
    res/drawable-xhdpi/notification_icon.png:drawable-xhdpi/notification_icon.png,
    res/drawable-xxhdpi/notification_icon.png:drawable-xxhdpi/notification_icon.png

# Android permissions
android.permissions = 
    WRITE_EXTERNAL_STORAGE,
    READ_EXTERNAL_STORAGE,
    RECORD_AUDIO,
    MODIFY_AUDIO_SETTINGS,
    SET_WALLPAPER,
    VIBRATE,
    FOREGROUND_SERVICE,
    RECEIVE_BOOT_COMPLETED,
    WAKE_LOCK,
    POST_NOTIFICATIONS,
    START_FOREGROUND_SERVICE_FROM_BACKGROUND,
    USE_FULL_SCREEN_INTENT,
    REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
    SCHEDULE_EXACT_ALARM,
    USE_EXACT_ALARM,
    BROADCAST_PACKAGE_REMOVED,
    BROADCAST_STICKY,
    INTERNET,
    ACCESS_NETWORK_STATE,
    ACCESS_FINE_LOCATION,
    ACCESS_COARSE_LOCATION

# Service configuration
services = BGTaskService:service/main.py:foreground:sticky:ongoing:persistent:boot_completed
android.service_type = shortService

# Activity and runtime settings
android.entrypoint = org.kivy.android.PythonActivity
android.activity_launch_mode = singleTask
android.wakelock = True
android.allow_background_activity = True
android.allow_background_service = True

# Python settings
android.optimize_python = True
android.precompile_python = True

# Dependencies
android.gradle_dependencies = 
    androidx.core:core:1.6.0,
    androidx.appcompat:appcompat:1.3.0
android.enable_androidx = True

# Network security for HTTPS tile requests
android.add_meta_data = android.webkit.WebView.EnableSafeBrowsing=false

android.add_services = 
    service/service_communication_manager.py:android.broadcast.BroadcastReceiver
