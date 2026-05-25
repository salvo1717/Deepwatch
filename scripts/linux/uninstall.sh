#!/bin/bash

echo "=========================================================="
echo "  RIMOZIONE AMBIENTE E MODELLI"
echo "=========================================================="
echo ""
echo "Questo script eliminerà l'ambiente virtuale (venv)"
echo "e i modelli IA scaricati/generati per liberare spazio."
echo "I tuoi file di codice non verranno toccati."
echo ""
read -p "Premi Invio per continuare o CTRL+C per annullare..."

echo ""
echo "Passaggio alla cartella principale..."
cd "$(dirname "$0")/../.." || exit

echo ""
echo "Rimozione cartella venv in corso..."
if [ -d "venv" ]; then
    rm -rf venv
fi

echo "Rimozione modelli YOLO in corso..."
# Controlla sia nella root che nella cartella models
[ -f "models/yolov8s-worldv2.pt" ] && rm -f "models/yolov8s-worldv2.pt"
[ -f "models/yolov8s-worldv2_jolly.onnx" ] && rm -f "models/yolov8s-worldv2_jolly.onnx"
[ -d "models/yolov8s-worldv2_openvino_model" ] && rm -rf "models/yolov8s-worldv2_openvino_model"
[ -f "yolov8s-worldv2.pt" ] && rm -f "yolov8s-worldv2.pt"
[ -f "yolov8s-worldv2_jolly.onnx" ] && rm -f "yolov8s-worldv2_jolly.onnx"
[ -d "yolov8s-worldv2_openvino_model" ] && rm -rf "yolov8s-worldv2_openvino_model"

echo "Rimozione configurazioni locali e log..."
[ -d "config" ] && rm -rf "config"
[ -f "crash_report.txt" ] && rm -f "crash_report.txt"
[ -f "dashboard_init_error.txt" ] && rm -f "dashboard_init_error.txt"

echo "Pulizia cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo ""
echo "=========================================================="
echo "  PULIZIA COMPLETATA CON SUCCESSO!"
echo "=========================================================="
echo "Lo spazio su disco è stato liberato."
