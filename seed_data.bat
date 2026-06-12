@echo off
cd /d %~dp0
set PYTHON=%LOCALAPPDATA%\Python\bin\python.exe
if not exist "%PYTHON%" set PYTHON=python
"%PYTHON%" scripts\seed_patients.py
pause
