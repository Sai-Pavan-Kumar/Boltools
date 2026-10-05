@echo off
title Boltools Desktop Suite
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "main.py"
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" "main.py"
) else (
    start "" python "main.py"
)
