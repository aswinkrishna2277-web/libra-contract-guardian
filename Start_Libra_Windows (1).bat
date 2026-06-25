@echo off
REM ============================================================================
REM  Libra Contract Guardian v2.0 - Windows launcher
REM  Double-click this file to start the application.
REM ============================================================================

cd /d "%~dp0"

echo.
echo  ========================================================
echo   Libra Contract Guardian v2.0
echo  ========================================================
echo.

REM --- Check the virtual environment exists ---
if not exist "venv\Scripts\activate.bat" goto :setup
goto :activate

:setup
echo  [setup] No virtual environment found. Creating one now...
python -m venv venv
if errorlevel 1 goto :nopython
call "venv\Scripts\activate.bat"
echo  [setup] Installing dependencies on first run, please wait...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 goto :nodeps
goto :run

:activate
call "venv\Scripts\activate.bat"
goto :run

:run
echo.
echo  Checking your environment...
python check_setup.py
echo.
echo  Starting Libra. A browser tab will open shortly.
echo  To stop the app, close this window or press Ctrl+C.
echo.
streamlit run app.py
goto :end

:nopython
echo.
echo  ERROR: Could not create the virtual environment.
echo  Please confirm Python 3.11 or newer is installed and on your PATH.
echo  Download from https://www.python.org/downloads/
echo.
pause
exit /b 1

:nodeps
echo.
echo  ERROR: Dependency installation failed. See the messages above.
echo.
pause
exit /b 1

:end
pause
