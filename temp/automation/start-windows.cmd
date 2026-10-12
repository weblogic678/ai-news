@echo off
cd /d "%~dp0"
py -3 run.py init
if errorlevel 1 goto failed
py -3 run.py audit
if errorlevel 1 goto failed
py -3 run.py report
if errorlevel 1 goto failed
start "" "work\report.html"
echo Report is ready. See README.md for generate and export commands.
pause
exit /b 0
:failed
echo Failed. Python 3.10+ is required. See README.md.
pause
exit /b 1
