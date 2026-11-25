@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 main.py
) else (
    python main.py
)

if errorlevel 1 (
    echo.
    echo Color Gang Shimeji encountered an error.
    pause
)
