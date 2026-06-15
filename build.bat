@echo off
setlocal
title SDBA - Build

echo.
echo  ============================================================
echo    SDBA - Stagic Data Breach Alert  ^|  Windows Build Script
echo  ============================================================
echo.

:: ── Kill any running uvicorn/Python that might lock files ─────────────────────
echo  Stopping any running SDBA/uvicorn processes...
taskkill /F /IM uvicorn.exe /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq SDBA*" /T >nul 2>&1
timeout /t 1 /nobreak >nul

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

:: --user avoids touching locked files in the system Scripts folder
py -m pip install --quiet --user ^
    fastapi "uvicorn[standard]" aiosqlite "httpx[http2]" ^
    dnspython pydantic-settings ipwhois colorama socksio ^
    pyinstaller

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: pip install failed. See output above.
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
echo  Your executable is ready:
echo    %~dp0backend\dist\SDBA.exe
echo.
echo  Double-click SDBA.exe to launch.
echo  A browser window will open automatically at http://127.0.0.1:8000
echo.
pause
endlocal
