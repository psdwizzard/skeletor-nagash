@echo off
rem Skeletor Nagash uninstaller - double-click me.
powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0uninstall.ps1"
if errorlevel 1 pause
