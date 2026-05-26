#!/bin/bash
cd "$(dirname "$0")/../.."
if [ ! -d "venv" ]; then
    echo "[X] Errore: Ambiente virtuale non trovato."
    echo "Per favore, esegui prima 'bash scripts/linux/installazione.sh'."
    exit 1
fi

source venv/bin/activate

# Controllo rapido se le dipendenze base sono installate (senza importarle)
if ! python3 -c "import importlib.metadata; [importlib.metadata.version(pkg) for pkg in ['ultralytics', 'opencv-python', 'PyQt6']]" &> /dev/null; then
    echo "[X] Errore: Le dipendenze non sembrano essere installate correttamente."
    echo "Per favore, esegui prima 'bash scripts/linux/installazione.sh'."
    exit 1
fi

python3 main.py
