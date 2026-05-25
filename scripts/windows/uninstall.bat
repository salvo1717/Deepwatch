@echo off
title Disinstallazione / Pulizia Progetto
cls

echo ==========================================================
echo   RIMOZIONE AMBIENTE E MODELLI
echo ==========================================================
echo.
echo Questo script eliminera' l'ambiente virtuale (venv) 
echo e i modelli IA scaricati/generati per liberare spazio.
echo I tuoi file di codice non verranno toccati.
echo.
pause

echo.
echo Passaggio alla cartella principale...
cd /d "%~dp0\..\.."

echo.
echo Rimozione cartella venv in corso...
if exist "venv" rmdir /s /q "venv"

echo Rimozione modelli YOLO in corso...
if exist "models\yolov8s-worldv2.pt" del /f /q "models\yolov8s-worldv2.pt"
if exist "models\yolov8s-worldv2_jolly.onnx" del /f /q "models\yolov8s-worldv2_jolly.onnx"
if exist "models\yolov8s-worldv2_openvino_model" rmdir /s /q "models\yolov8s-worldv2_openvino_model"
if exist "yolov8s-worldv2.pt" del /f /q "yolov8s-worldv2.pt"
if exist "yolov8s-worldv2_jolly.onnx" del /f /q "yolov8s-worldv2_jolly.onnx"
if exist "yolov8s-worldv2_openvino_model" rmdir /s /q "yolov8s-worldv2_openvino_model"

echo Rimozione configurazioni locali e log...
if exist "config" rmdir /s /q "config"
if exist "crash_report.txt" del /f /q "crash_report.txt"
if exist "dashboard_init_error.txt" del /f /q "dashboard_init_error.txt"
if exist "*.pyc" del /s /q "*.pyc"

echo Pulizia cache Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo.
echo ==========================================================
echo   PULIZIA COMPLETATA CON SUCCESSO!
echo ==========================================================
echo Lo spazio su disco e' stato liberato.
pause
