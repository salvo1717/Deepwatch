#!/bin/bash
cd "$(dirname "$0")/../.."
echo "=========================================================="
echo "  CONTROLLO SISTEMA E INSTALLAZIONE AUTOMATICA"
echo "=========================================================="

# Controllo Python3
if ! command -v python3 &> /dev/null; then
    echo "[X] Python3 NON trovato. Per favore installalo prima di continuare."
    exit 1
fi

# Controllo modulo venv
if ! python3 -m venv --help &> /dev/null; then
    echo "[X] Modulo 'python3-venv' NON trovato."
    echo "Su Ubuntu/Debian, esegui: sudo apt update && sudo apt install python3-venv"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creazione ambiente virtuale in corso..."
    python3 -m venv venv
fi

# Rendo eseguibili gli script
chmod +x scripts/linux/*.sh

source venv/bin/activate
python3 scripts/core/setup.py

echo ""
echo "=========================================================="
echo "  INSTALLAZIONE COMPLETATA!"
echo "=========================================================="
echo ""
echo "Puoi avviare il programma in futuro usando:"
echo "--> ./scripts/linux/run.sh"
echo ""
