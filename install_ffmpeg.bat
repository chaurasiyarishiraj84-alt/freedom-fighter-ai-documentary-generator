@echo off
echo ============================================================
echo  FFmpeg Installer for Windows
echo ============================================================

REM Try winget first
echo Trying winget...
winget install --id Gyan.FFmpeg -e --silent 2>nul
if %errorlevel% equ 0 (
    echo ✅ FFmpeg installed via winget
    goto :verify
)

REM Try chocolatey
echo Trying chocolatey...
choco install ffmpeg -y 2>nul
if %errorlevel% equ 0 (
    echo ✅ FFmpeg installed via chocolatey
    goto :verify
)

REM Manual download fallback
echo.
echo ❌ Auto-install failed.
echo.
echo MANUAL STEPS:
echo 1. Go to: https://www.gyan.dev/ffmpeg/builds/
echo 2. Download: ffmpeg-release-essentials.zip
echo 3. Extract to: C:\ffmpeg\
echo 4. Open: Control Panel → System → Advanced → Environment Variables
echo 5. Under "System Variables" find "Path" → Edit → New
echo 6. Add: C:\ffmpeg\bin
echo 7. Click OK → Restart terminal
echo.
pause
exit /b 1

:verify
echo.
echo Verifying...
ffmpeg -version 2>nul | findstr "ffmpeg version"
if %errorlevel% equ 0 (
    echo ✅ FFmpeg working!
    echo.
    echo Now run: python main.py
) else (
    echo ⚠️  FFmpeg installed but not in PATH yet.
    echo    Please CLOSE this terminal and open a NEW one.
    echo    Then run: python main.py
)
pause