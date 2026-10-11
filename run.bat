@echo off
setlocal
echo =======================================================
echo LAUNCHING BOLTOOLS DESKTOP APP (DEV MODE)
echo =======================================================

set BOLTOOLS_DEV=1

if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe main.py
) else (
    python main.py
)
