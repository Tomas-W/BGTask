[app]
title = BGTask
package.name = bgtask
package.domain = org.bgtask

source.dir = .

source.include_exts = py,png,json
source.exclude_exts = gitignore,md
source.exclude_dirs = bin

version = 0.1

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b

requirements = kivy,android.storage

android.optimize_python = True
android.precompile_python = True

android.archs = arm64-v8a
