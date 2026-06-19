@echo off
echo ============================================================
echo  STEP 1: Installing FFmpeg (required for video rendering)
echo ============================================================
winget install --id Gyan.FFmpeg -e --silent
if %errorlevel% neq 0 (
    echo winget failed, trying chocolatey...
    choco install ffmpeg -y
)

echo.
echo ============================================================
echo  STEP 2: Refreshing PATH
echo ============================================================
refreshenv 2>nul || echo "Restart terminal after this script if ffmpeg not found"

echo.
echo ============================================================
echo  STEP 3: Verifying ffmpeg
echo ============================================================
ffmpeg -version 2>nul | findstr "ffmpeg version"
if %errorlevel% neq 0 (
    echo.
    echo ❌ FFmpeg still not found in PATH.
    echo    Please RESTART your terminal/VS Code after install.
    echo    Then run: python main.py
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  STEP 4: Running pipeline
echo ============================================================
python main.py
pause