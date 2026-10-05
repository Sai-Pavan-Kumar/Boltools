@echo off
title Boltools Debug Console
cd /d "%~dp0"
echo ================================================
echo Starting Boltools Desktop Suite (Debug Mode)...
echo ================================================
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "main.py"
) else (
    python "main.py"
)
echo.
echo Process terminated.
pause
