@echo off
rem Skeletor Nagash installer - double-click me.
powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0install.ps1"
if errorlevel 1 pause
