@echo off
cd /d %~dp0
set PYTHON=%LOCALAPPDATA%\Python\bin\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo Using: %PYTHON%
"%PYTHON%" scripts\init_db.py
if errorlevel 1 (
    echo.
    echo Failed. Set DB password first, for example:
    echo   set DB_PASSWORD=your_postgres_password
    pause
    exit /b 1
)
echo.
echo Done. Tables created.
pause
