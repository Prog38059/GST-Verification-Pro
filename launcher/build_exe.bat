@echo off
title Build QuickHub Executable
echo ===================================================
echo       Building QuickHub Desktop Launcher .exe
echo ===================================================

cd /d "%~dp0"

IF NOT EXIST "..\venv\Scripts\pyinstaller.exe" (
    echo [ERROR] PyInstaller not found in venv.
    echo Run: ..\venv\Scripts\pip.exe install pyinstaller
    pause
    exit /b 1
)

echo Compiling launcher.py into standalone .exe ...
..\venv\Scripts\pyinstaller.exe --noconsole --onefile --name "QuickHub" --add-data "tools.json;." launcher.py

echo.
IF EXIST "dist\QuickHub.exe" (
    echo ===================================================
    echo SUCCESS! Standalone executable created:
    echo %~dp0dist\QuickHub.exe
    echo ===================================================
) ELSE (
    echo [ERROR] Build failed. Check the error log above.
)

pause
