@echo off
setlocal
cd /d "%~dp0"
if not exist demo_output mkdir demo_output
cd source
python engine_v013.py --seed 1217 --population 450 --years 1 --events-scale 0.08 --stop-week 52 --db ..\demo_output\demo.sqlite --out ..\demo_output\reports --quiet
if errorlevel 1 (echo SIMULATION FAILED & pause & exit /b 1)
python audit_v013.py ..\demo_output\demo.sqlite --output ..\demo_output\audit.json
if errorlevel 1 (echo INDEPENDENT DATABASE AUDIT FAILED & pause & exit /b 1)
echo.
echo COMPLETED. Find results in demo_output\reports and demo_output\audit.json
pause
