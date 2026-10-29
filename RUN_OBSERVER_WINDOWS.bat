@echo off
rem Golf Legacy observer: double-click to start it and open it in your browser.
rem Worlds live in the "worlds" folder next to this file. Stop with Ctrl-C in this window
rem (a running advance finishes its week and saves first) or the Quit button in the World library.
cd /d "%~dp0"
title Golf Legacy observer
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 tools\observer.py --open %*
) else (
    python tools\observer.py --open %*
)
echo.
echo The observer has stopped. You can close this window.
pause
