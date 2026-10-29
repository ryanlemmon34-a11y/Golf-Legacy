@echo off
rem Golf Legacy benchmark: times "To end of season" on this computer, as the observer does it, and
rem writes everything to benchmark_result.txt next to this file. It uses temporary copies only.
rem   Double-click:            season 1 of a new world, with all logical CPUs as workers, then half of them.
rem   Drag a world folder on:  that world (for example the 50-season world_2027), on a temporary copy.
rem Plug the laptop in and close other programs first; it takes about 5 minutes (longer for a big world).
cd /d "%~dp0"
title Golf Legacy benchmark
set PY=python
where py >nul 2>nul
if %errorlevel%==0 set PY=py -3
set /a HALF=%NUMBER_OF_PROCESSORS%/2
if "%~1"=="" goto newworld
echo Measuring a season skip on a temporary copy of "%~1" ...
%PY% tools\benchmark_skip.py --from-world "%~1" --log benchmark_result.txt
goto done
:newworld
echo Measuring season 1 of a new world with %NUMBER_OF_PROCESSORS% workers, then %HALF% ...
%PY% tools\benchmark_skip.py --log benchmark_result.txt
%PY% tools\benchmark_skip.py --workers %HALF% --log benchmark_result.txt
:done
echo.
echo Finished. The results are in benchmark_result.txt in this folder: attach that file to Claude.
pause
