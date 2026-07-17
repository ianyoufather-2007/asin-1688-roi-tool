@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
py -m asin_1688_roi.gui
pause
