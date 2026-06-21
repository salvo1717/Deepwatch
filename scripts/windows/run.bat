@echo off
cd /d "%~dp0\..\.."
set PYTHONUTF8=1
if not exist "venv" (
    echo [X] Errore: Ambiente virtuale non trovato. 
    echo Per favore, esegui prima 'scripts\windows\installazione.bat'.
    pause
    exit
)

start "" "venv\Scripts\pythonw.exe" "main.py"
exit
