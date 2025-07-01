
; Path to startup folder Windows 10 = C:\Users\${user.name}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup

#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode("Input") ; Sets the sending method to the "Input" mode.
SetWorkingDir A_ScriptDir ; Ensures a consistent starting directory.
SetCapsLockState "AlwaysOff"
CapsLock::Send "{Alt Down}{Shift Down}{Shift Up}{Alt Up}"