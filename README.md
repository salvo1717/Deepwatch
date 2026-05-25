# 🛡️ DEEPWATCH - AI Security System

![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-WorldV2-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)
![Hardware](https://img.shields.io/badge/Hardware-CUDA%20%7C%20DirectML%20%7C%20OpenVINO%20%7C%20MPS-success.svg)

Un sistema di visione artificiale avanzato e modulare basato su **YOLOv8**, progettato per il monitoraggio simultaneo e il rilevamento in tempo reale di oggetti e persone tramite flussi video multipli.

---

## ✨ Funzionalità Principali

- **Monitoraggio Multi-Camera Simultaneo:** Capacità di gestire più flussi video in parallelo. Le telecamere possono monitorare l'ambiente in background anche quando non sono visualizzate direttamente.
- **Rilevamento Intelligente dell'Hardware:** Analisi automatica dell'hardware host per configurare l'ambiente di esecuzione ottimale (NVIDIA CUDA, AMD DirectML, Intel OpenVINO, Apple Metal MPS o CPU).
- **Gestione Asincrona dei Flussi:** Cambio telecamera fluido e non bloccante. L'interfaccia rimane reattiva durante le operazioni hardware lente grazie a un'architettura multi-thread.
- **Visual Detection Logs:** Sistema di log avanzato basato su **MongoDB** che memorizza screenshot e metadati dei rilevamenti (data, ora, oggetti, confidenza).
- **Dettaglio Log in Alta Risoluzione:** Funzione di ispezione dei log che permette di visualizzare le catture a tutto schermo con dettagli tecnici completi.
- **Filtro Visione Notturna:** Algoritmo CLAHE nello spazio colore LAB per il miglioramento della visibilità in condizioni di scarsa illuminazione.
- **Architettura Enterprise:** Codice suddiviso in pacchetti logici (`core`, `ui`, `models`, `utils`) per massima manutenibilità.

---

## 🚀 Prerequisiti

- **OS:** Windows 10/11 o Linux.
- **Python:** Versione 3.11 o superiore.
- **Database:** MongoDB (Locale o Atlas).
- **Webcam:** Almeno un dispositivo di acquisizione video connesso.

---

## 🛠️ Installazione

Il progetto utilizza un installer dinamico che configura automaticamente l'ambiente virtuale e le dipendenze hardware-specifiche.

### Windows
1. Clona il repository.
2. Crea un file `.env` con la tua `MONGODB_URI`.
3. Fai doppio clic su `scripts\windows\installazione.bat`.

### Linux
1. Clona il repository.
2. Crea un file `.env` con la tua `MONGODB_URI`.
3. Esegui: `chmod +x scripts/linux/installazione.sh && ./scripts/linux/installazione.sh`

---

## 💻 Utilizzo

Lancia il programma utilizzando i launcher dedicati:
- **Windows:** `scripts\windows\run.bat`
- **Linux:** `./scripts/linux/run.sh`

### Controlli Interfaccia
- **Dashboard**: Vista generale e accesso rapido alle funzioni.
- **Live View**: Visualizzazione in tempo reale con selettore camera asincrono.
- **Monitoraggio**: Interruttore per attivare l'analisi IA costante (anche in background).
- **Logs**: Galleria visuale dei rilevamenti con pulsante di visualizzazione dettagliata.

---

## 📂 Struttura del Progetto

```text
.
├── main.py                 # Orchestratore e punto di ingresso
├── models/                 # Modelli IA (YOLOv8 WorldV2)
├── scripts/                # Script di automazione (Win/Linux)
├── config/                 # Stato persistente dell'app
├── src/                    
│   ├── core/               # IA, Camera Manager, Video Threads
│   ├── ui/                 # Interfaccia PyQt6 (Views, Components, Theme)
│   ├── models/             # Schemi database (Beanie/Pydantic)
│   └── utils/              # Manager DB e Image Processing
└── .env                    # Configurazioni sensibili (non committato)
```

---

## ⚙️ Hardware AI Acceleration

Il sistema seleziona automaticamente il backend più veloce:
1. **NVIDIA CUDA:** Tensor cores acceleration.
2. **OpenVINO:** Ottimizzazione Intel per iGPU e CPU.
3. **DirectML:** Supporto GPU AMD su Windows.
4. **MPS:** Apple Silicon support.

---

*DEEPWATCH è progettato per garantire sicurezza e reattività, offrendo una soluzione professionale per la video sorveglianza assistita da IA.*
