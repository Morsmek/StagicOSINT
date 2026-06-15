@echo off
setlocal
title SDBA - Build

echo.
echo  ============================================================
echo    SDBA — Stagic Data Breach Alert  ^|  Windows Build Script
echo  ============================================================
echo.

:: ── Step 1: Build the React frontend ─────────────────────────────────────────
echo [1/4] Building React frontend...
cd /d "%~dp0frontend"

call npm install
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: npm install failed.
    echo  Make sure Node.js is installed: https://nodejs.org
    pause & exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: npm run build failed. See output above.
    pause & exit /b 1
)
echo  React frontend built successfully.
echo.

:: ── Step 2: Install Python deps + PyInstaller ────────────────────────────────
echo [2/4] Installing Python dependencies...
cd /d "%~dp0backend"

py -m pip install --quiet --upgrade ^
    fastapi "uvicorn[standard]" aiosqlite "httpx[http2]" ^
    dnspython pydantic-settings ipwhois colorama socksio ^
    pyinstaller

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: pip install failed.
    echo  Make sure Python is installed: https://www.python.org
    pause & exit /b 1
)
echo  Python dependencies installed.
echo.

:: ── Step 3: Bundle with PyInstaller ──────────────────────────────────────────
echo [3/4] Bundling with PyInstaller (this takes ~30-60 seconds)...

py -m PyInstaller SDBA.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: PyInstaller failed. See output above for details.
    pause & exit /b 1
)
echo  Bundling complete.
echo.

:: ── Step 4: Done ─────────────────────────────────────────────────────────────
echo [4/4] Build complete!
echo.
echo  ┌──────────────────────────────────────────────────────────┐
echo  │  Your executable is ready:                               │
echo  │                                                          │
echo  │    %~dp0backend\dist\SDBA.exe
echo  │                                                          │
echo  │  Double-click SDBA.exe to launch.                        │
echo  │  A browser window will open automatically.               │
echo  └──────────────────────────────────────────────────────────┘
echo.
pause
endlocal
