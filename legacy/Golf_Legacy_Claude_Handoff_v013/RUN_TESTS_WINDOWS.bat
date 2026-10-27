@echo off
setlocal
cd /d "%~dp0source"
python -m unittest discover -s tests -v
set RESULT=%ERRORLEVEL%
echo.
if %RESULT% NEQ 0 (echo TESTS FAILED with code %RESULT%) else (echo ALL MAIN TESTS PASSED)
pause
exit /b %RESULT%
