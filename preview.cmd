@echo off
cd /d "%~dp0"
if exist "E:\Anaconda\python.exe" (
  "E:\Anaconda\python.exe" tools\preview.py
) else (
  python tools\preview.py
)
pause
