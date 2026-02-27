@echo off
REM ============================================================================
REM SnapLoad Build Script
REM Builds the SnapLoad executable using PyInstaller (onedir mode)
REM ============================================================================

setlocal enabledelayedexpansion

REM Get the directory of this script
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set BUILD_DIR=%SCRIPT_DIR%

:BUILD_START
echo.
echo ============================================================================
echo SnapLoad Release Build Script
echo ============================================================================
echo.
echo Project Directory: %PROJECT_DIR%
echo Build Directory: %BUILD_DIR%
echo Mode: RELEASE (onedir)
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
echo Starting Build...
echo ============================================================================
echo.

REM Change to build directory
cd /d "%BUILD_DIR%"

REM Run PyInstaller with the spec file
echo Building SnapLoad executable...
pyinstaller snapload.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Build completed successfully!
echo ============================================================================
echo.
echo Output directory: %BUILD_DIR%\dist\SnapLoad
echo Executable: %BUILD_DIR%\dist\SnapLoad\SnapLoad.exe
echo.
echo This is a RELEASE version with:
echo   - Onedir mode (directory with all dependencies)
echo   - No console window
echo.
echo For debugging, use build-debug.bat instead.
echo.

REM Ask if user wants to rebuild
echo.
set /p REBUILD="Do you want to rebuild (overwrite)? (y/n): "
if /i "%REBUILD%"=="y" (
    cls
    goto BUILD_START
)

echo.
echo Build script finished.
pause