@echo off
REM Battery Monitor Launcher for Windows
REM Simply double-click this file to start the battery monitor

echo Starting Wireless Device Battery Monitor...
echo.

python device_settings_gui.py

if errorlevel 1 (
    echo.
    echo Error: Python not found or script failed
    echo Make sure Python is installed and in your PATH
    echo.
    pause
)
