@echo off
setlocal
title StagicOSINT - Build

echo.
echo  ================================================
echo    StagicOSINT - Build Script
echo  ================================================
echo.

:: ── Step 1: Build the React frontend ────────────────────────────────────────
echo [1/4] Building React frontend...
cd /d "%~dp0frontend"

call npm install
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: npm install failed. Is Node.js installed?
    pause & exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: npm run build failed.
    pause & exit /b 1
)
echo  React frontend built successfully.
echo.

:: ── Step 2: Install Python deps including PyInstaller ───────────────────────
echo [2/4] Installing Python dependencies...
cd /d "%~dp0backend"

py -m pip install --quiet --upgrade ^
    fastapi uvicorn[standard] aiosqlite httpx ^
    dnspython pydantic-settings ipwhois ^
    pyinstaller

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: pip install failed.
    pause & exit /b 1
)
echo  Python dependencies installed.
echo.

:: ── Step 3: Run PyInstaller ─────────────────────────────────────────────────
echo [3/4] Bundling with PyInstaller...

py -m PyInstaller StagicOSINT.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: PyInstaller failed. See output above for details.
    pause & exit /b 1
)
echo  PyInstaller finished.
echo.

:: ── Step 4: Done ─────────────────────────────────────────────────────────────
echo [4/4] Build complete!
echo.
echo  Your executable is at:
echo    %~dp0backend\dist\StagicOSINT.exe
echo.
echo  Double-click it to launch StagicOSINT.
echo  A browser window will open automatically.
echo.
pause
endlocal
