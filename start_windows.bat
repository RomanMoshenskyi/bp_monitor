@echo off
cd /d %~dp0
set PYTHON=%LOCALAPPDATA%\Python\bin\python.exe
if not exist "%PYTHON%" set PYTHON=python

"%PYTHON%" -m pip install -r requirements.txt
"%PYTHON%" main.py
pause
