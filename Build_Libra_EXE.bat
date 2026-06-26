@echo off
REM ============================================================================
REM  Build_Libra_EXE.bat — builds a standalone Windows bundle of Libra.
REM  Run from inside the project folder with the venv active.
REM  Output: dist\Libra\Libra.exe  (plus supporting files)
REM ============================================================================

cd /d "%~dp0"

echo.
echo  Building Libra standalone bundle...
echo  This takes several minutes and produces a large folder.
echo.

if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"

pip show pyinstaller >nul 2>&1
if errorlevel 1 goto :install_pyi
goto :build

:install_pyi
echo  Installing PyInstaller...
pip install pyinstaller
goto :build

:build
pyinstaller Libra.spec --clean --noconfirm

echo.
if exist "dist\Libra\Libra.exe" goto :ok
goto :fail

:ok
echo  BUILD COMPLETE.
echo  The bundled app is in:  dist\Libra\
echo  Run it by double-clicking:  dist\Libra\Libra.exe
echo.
echo  Reminder: the end user still needs Ollama installed separately
echo  from https://ollama.com for full AI analysis.
goto :end

:fail
echo  BUILD DID NOT PRODUCE Libra.exe — check the messages above for errors.
goto :end

:end
echo.
pause
