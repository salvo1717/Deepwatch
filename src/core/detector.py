import os
import platform
import torch
import threading
from ultralytics import YOLO
from src.config.settings import OGGETTI_DA_RILEVARE, PATH_MODELLO_DEFAULT, PATH_MODELLO_ONNX, FOLDER_MODELLO_OPENVINO

class Detector:
    def __init__(self):
        self.device = None
        self.risoluzione = 640
        self.path_modello = PATH_MODELLO_DEFAULT
        self.os_name = platform.system()
        self.model = None
        self.lock = threading.Lock()
        
        self._rileva_hardware()
        self._carica_modello()

    def _rileva_hardware(self):
        """Rileva l'hardware disponibile e configura il dispositivo e la risoluzione."""
        providers_disponibili = []
        try:
            import onnxruntime as ort
            providers_disponibili = ort.get_available_providers()
        except: pass

        has_openvino = False
        try:
            import openvino as ov
            has_openvino = True
        except: pass

        if torch.cuda.is_available():
            print(f"MODALITÀ: NVIDIA CUDA ({torch.cuda.get_device_name(0)})")
            self.device = 0
            self.risoluzione = 960
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("MODALITÀ: Apple Metal (MPS)")
            self.device = "mps"
            self.risoluzione = 640
        elif "DmlExecutionProvider" in providers_disponibili and self.os_name == "Windows":
            print("MODALITÀ: DirectML (AMD GPU)")
            self.path_modello = PATH_MODELLO_ONNX
            self._esporta_onnx_se_necessario()
            self.device = None
            self.risoluzione = 640
        elif has_openvino:
            print("MODALITÀ: OpenVINO")
            self._esporta_openvino_se_necessario()
            
            import openvino as ov
            core = ov.Core()
            if "GPU" in core.available_devices:
                print("   -> Accelerazione: Intel Arc/Iris iGPU (via OpenVINO)")
                self.device = "cpu" 
                self.risoluzione = 640
            else:
                print("   -> Accelerazione: CPU")
                self.device = "cpu"
                self.risoluzione = 640
            
            self.path_modello = FOLDER_MODELLO_OPENVINO
        else:
            print("MODALITÀ: CPU Standard")
            self.device = "cpu"
            self.risoluzione = 640

    def _esporta_onnx_se_necessario(self):
        if not os.path.exists(self.path_modello):
            print("   [!] Esportazione modello per DirectML in corso...")
            tmp = YOLO(PATH_MODELLO_DEFAULT)
            tmp.set_classes(OGGETTI_DA_RILEVARE)
            tmp.export(format="onnx")
            if os.path.exists("yolov8s-worldv2.onnx"): 
                os.rename("yolov8s-worldv2.onnx", self.path_modello)

    def _esporta_openvino_se_necessario(self):
        if not os.path.exists(FOLDER_MODELLO_OPENVINO):
            print("   [!] Esportazione modello per OpenVINO in corso (una tantum)...")
            model = YOLO(PATH_MODELLO_DEFAULT)
            model.set_classes(OGGETTI_DA_RILEVARE)
            model.export(format="openvino", half=True, dynamic=True, device="cpu", imgsz=640, batch=1, simplify=True)

    def _carica_modello(self):
        """Carica il modello YOLO con le impostazioni rilevate."""
        try:
            if str(self.path_modello).endswith(".pt"):
                self.model = YOLO(self.path_modello)
                self.model.set_classes(OGGETTI_DA_RILEVARE)
            else:
                self.model = YOLO(self.path_modello, task='detect')
        except Exception as e:
            print(f"Errore caricamento modello specifico ({e}), ripiego su default...")
            self.model = YOLO(PATH_MODELLO_DEFAULT)
            self.model.set_classes(OGGETTI_DA_RILEVARE)

    def predict(self, frame):
        """Esegue il rilevamento su un frame con locking per thread safety."""
        with self.lock:
            return self.model.predict(
                frame, 
                verbose=False, 
                conf=0.50, 
                imgsz=self.risoluzione, 
                device=self.device
            )
