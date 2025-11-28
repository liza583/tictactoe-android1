[app]
title = Крестики-Нолики
package.name = tictactoe
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0
requirements = python3,kivy

orientation = portrait

[buildozer]
log_level = 2

[android]
api = 33
minapi = 21
permissions = INTERNET
android.allow_backup = true
