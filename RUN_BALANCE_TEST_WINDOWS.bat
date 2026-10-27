@echo off
cd /d "%~dp0"
python tools\balance_test.py
echo.
echo Report written to reports\BALANCE_REPORT.md
pause
