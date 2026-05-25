import os
import platform

# --- CONFIGURAZIONE AMBIENTE ---
def setup_environment():
    """Configura le variabili d'ambiente per silenziare i log e ottimizzare le prestazioni."""
    os.environ["OPENCV_LOG_LEVEL"] = "OFF"
    os.environ["NNPACK_DISABLE"] = "1"
    os.environ["ULTRALYTICS_UPDATE"] = "False"

    # Fix per Linux/Wayland
    if platform.system() == "Linux":
        os.environ["QT_QPA_PLATFORM"] = "xcb"

# --- COSTANTI ---
OGGETTI_DA_RILEVARE = [
    "person", "face", "hand",           # Identità
    "glasses", "hat", "cap",            # Tratti distintivi
    "watch", "cell phone",              # Oggetti di valore
    "backpack", "handbag", "suitcase",  # Bagagli
    "knife",                            # Minacce
    "car", "motorcycle",                # Veicoli
    "dog", "cat"                        # Filtraggio domestico
]

PATH_MODELLO_DEFAULT = "models/yolov8s-worldv2.pt"
PATH_MODELLO_ONNX = "models/yolov8s-worldv2_jolly.onnx"
FOLDER_MODELLO_OPENVINO = "models/yolov8s-worldv2_openvino_model"
