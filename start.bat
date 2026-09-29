@echo off
title GST Verification Pro
echo ===================================================
echo       Starting GST Verification Pro App...
echo ===================================================

cd /d "%~dp0"

IF NOT EXIST "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in %~dp0venv!
    echo Please create it first: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting server on http://127.0.0.1:5000 ...
start "" http://127.0.0.1:5000

.\venv\Scripts\python.exe app.py
pause
