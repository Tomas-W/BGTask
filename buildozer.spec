[app]
title = BGTask
package.name = bgtask
package.domain = org.bgtask

source.dir = .

source.include_exts = py,png,json
source.exclude_exts = gitignore,md

version = 0.1

orientation = portrait

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b

requirements = kivy,android.storage

android.optimize_python = True
android.precompile_python = True

android.archs = arm64-v8a

# p4a.java_build_tool = javac
# p4a.java_home = /usr/lib/jvm/java-17-openjdk-amd64
# 
# p4a.bootstrap = sdl2
# p4a.local_recipes = ~/.buildozer/prebuild/