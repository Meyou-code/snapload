@echo off
REM ============================================================================
REM SnapLoad Debug Build Script
REM Builds the SnapLoad DEBUG executable using PyInstaller (onedir mode)
REM Console window will be shown for debugging
REM ============================================================================

setlocal enabledelayedexpansion

REM Get the directory of this script
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set BUILD_DIR=%SCRIPT_DIR%

echo.
echo ============================================================================
echo SnapLoad Debug Build Script
echo ============================================================================
echo.
echo Project Directory: %PROJECT_DIR%
echo Build Directory: %BUILD_DIR%
echo Mode: DEBUG (onedir with console)
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)
echo [OK] Python is installed

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PyInstaller is not installed. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller is installed

echo.
echo ============================================================================
echo Starting Debug Build...
echo ============================================================================
echo.

REM Change to build directory
cd /d "%BUILD_DIR%"

REM Run PyInstaller with the debug spec file
echo Building SnapLoad DEBUG executable (onedir)...
pyinstaller snapload-debug.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Debug build completed successfully!
echo ============================================================================
echo.
echo Output directory: %BUILD_DIR%\dist\SnapLoad-Debug
echo Executable: %BUILD_DIR%\dist\SnapLoad-Debug\SnapLoad-Debug.exe
echo.
echo This is a DEBUG version with:
echo   - Onedir mode (directory with all dependencies)
echo   - Console window for debugging output
echo.

REM Optional: Open the output directory
echo.
set /p OPEN_OUTPUT="Do you want to open the output directory? (y/n): "
if /i "%OPEN_OUTPUT%"=="y" (
    start explorer "%BUILD_DIR%\dist"
)

pause
