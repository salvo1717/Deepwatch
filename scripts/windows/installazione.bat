@echo off
setlocal enabledeladedelexpansion
cd /d "%~dp0\..\.."
title Setup Progetto Sorveglianza AI
cls

echo ==========================================================
echo   CONTROLLO SISTEMA E INSTALLAZIONE AUTOMATICA
echo ==========================================================

set "PYTHON_CMD=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python NON trovato. Scarico installer...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo Installazione in corso...
    start /wait python_installer.exe /quiet PrependPath=1 Include_test=0 InstallAllUsers=0
    del python_installer.exe
    echo Per favore, CHIUDI questa finestra e RIAPRI il file .bat
    pause
    exit
)

if not exist "venv" (
    echo Creazione ambiente virtuale in corso...
    "%PYTHON_CMD%" -m venv venv
)

call venv\Scripts\activate
:: Esegue setup.py per verificare le dipendenze
python scripts\core\setup.py
echo.
echo ==========================================================
echo   INSTALLAZIONE COMPLETATA!
echo ==========================================================
echo.
echo Puoi avviare il programma in futuro usando:
echo --^> scripts\windows\run.bat
echo.
