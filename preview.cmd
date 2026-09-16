@echo off
setlocal
cd /d "%~dp0"
if exist "E:\Anaconda\python.exe" (
    "E:\Anaconda\python.exe" tools\preview.py --serve
) else (
    python tools\preview.py --serve
)
pause
