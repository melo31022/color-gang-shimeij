@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

%PYTHON% -c "import PIL" >nul 2>nul
if errorlevel 1 (
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Failed to install Python dependencies.
        pause
        exit /b 1
    )
)

%PYTHON% main.py
if errorlevel 1 (
    echo.
    echo Color Gang Shimeji encountered an error.
    pause
)
