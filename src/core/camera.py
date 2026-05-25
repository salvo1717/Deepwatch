import cv2
import platform
import json
import os
import ctypes
import threading
import time
from datetime import datetime

try:
    from pygrabber.dshow_graph import FilterGraph
    HAS_PYGRABBER = True
except ImportError:
    HAS_PYGRABBER = False

class Camera:
    def __init__(self, target_index=0):
        self.caps = {} # index -> VideoCapture
        self.caps_lock = threading.Lock() # Protegge l'accesso al dizionario self.caps
        self.cam_locks = {} # index -> Lock (protegge le operazioni sulla singola camera)
        self.os_name = platform.system()
        self.state_file = "config/app_state.json"
        os.makedirs("config", exist_ok=True)
        
        # Cache per le camere per evitare lag
        self._cached_cameras = []
        self._last_scan_time = 0
        
        # Carica indice e stati salvati
        self.app_state = self._load_state()
        self.current_index = target_index if target_index is not None else self.app_state.get("last_camera_index", 0)
        self.monitoring_states = self.app_state.get("monitoring_states", {})
        
        # Inizializzazione della camera principale
        self._open_camera(self.current_index)

    def _get_cam_lock(self, index):
        with self.caps_lock:
            if index not in self.cam_locks:
                self.cam_locks[index] = threading.Lock()
            return self.cam_locks[index]

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_state(self):
        try:
            self.app_state["last_camera_index"] = self.current_index
            self.app_state["monitoring_states"] = self.monitoring_states
            with open(self.state_file, "w") as f:
                json.dump(self.app_state, f, indent=4)
        except: pass

    def set_monitoring(self, index, active):
        """Salva lo stato di monitoraggio per una camera specifica."""
        name = self.get_camera_name(index)
        with self.caps_lock:
            self.monitoring_states[name] = active
        self._save_state()

    def get_monitoring(self, index):
        """Recupera lo stato di monitoraggio per una camera specifica."""
        name = self.get_camera_name(index)
        with self.caps_lock:
            return self.monitoring_states.get(name, False)

    def set_monitoring_for_current(self, active):
        self.set_monitoring(self.current_index, active)

    def get_monitoring_for_current(self):
        return self.get_monitoring(self.current_index)

    def _open_camera(self, index):
        """Apre la camera specificata in modo sicuro con locking per-camera."""
        lock = self._get_cam_lock(index)
        with lock:
            # Check se è già aperta
            with self.caps_lock:
                if index in self.caps and self.caps[index].isOpened():
                    return True

            try:
                if self.os_name == "Windows":
                    ctypes.windll.ole32.CoInitialize(None)

                backends = []
                if self.os_name == "Windows":
                    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
                elif self.os_name == "Linux":
                    backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
                else:
                    backends = [cv2.CAP_ANY]

                cap = None
                opened = False
                for backend in backends:
                    cap = cv2.VideoCapture(index, backend)
                    if cap and cap.isOpened():
                        opened = True
                        break
                    if cap: cap.release()
                
                if not opened:
                    cap = cv2.VideoCapture(index)
                    opened = cap.isOpened()

                if opened:
                    # Ottimizzazioni per stabilità
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    for _ in range(2): cap.read() # Svuota buffer iniziale

                    with self.caps_lock:
                        self.caps[index] = cap
                    return True
                
                return False
            except Exception as e:
                print(f"⚠️ Errore apertura camera {index}: {e}")
                return False

    def get_available_cameras(self, force_scan=False):
        now = time.time()
        if not force_scan and self._cached_cameras and (now - self._last_scan_time < 30):
            return self._cached_cameras

        raw_cameras = []
        if self.os_name == "Windows" and HAS_PYGRABBER:
            try:
                ctypes.windll.ole32.CoInitialize(None)
                graph = FilterGraph()
                for i, name in enumerate(graph.get_input_devices()):
                    raw_cameras.append({'index': i, 'name': name})
            except: pass
            
        if not raw_cameras:
            for i in range(5):
                with self.caps_lock:
                    if i in self.caps:
                        raw_cameras.append({'index': i, 'name': f"Camera {i}"})
                        continue
                backend = cv2.CAP_V4L2 if self.os_name == "Linux" else (cv2.CAP_DSHOW if self.os_name == "Windows" else cv2.CAP_ANY)
                temp = cv2.VideoCapture(i, backend)
                if temp.isOpened():
                    raw_cameras.append({'index': i, 'name': f"Camera {i}"})
                    temp.release()

        virtual_keywords = ["virtual", "obs", "iriun", "droidcam", "splitcam", "pixel"]
        def sort_priority(cam):
            if cam['index'] == self.current_index: return 0
            name_lower = cam['name'].lower()
            if not any(kw in name_lower for kw in virtual_keywords): return 1
            return 2

        self._cached_cameras = sorted(raw_cameras, key=sort_priority)
        self._last_scan_time = now
        return self._cached_cameras

    def get_camera_name(self, index):
        cams = self.get_available_cameras()
        for c in cams:
            if c['index'] == index:
                return c['name']
        return f"Camera {index}"

    def get_current_name(self):
        return self.get_camera_name(self.current_index)

    def set_camera(self, index):
        success = self._open_camera(index)
        if success:
            self.current_index = index
            self._save_state()
        return success

    def read(self, index=None):
        if index is None: index = self.current_index
        lock = self._get_cam_lock(index)
        with lock:
            with self.caps_lock:
                cap = self.caps.get(index)
            if cap and cap.isOpened():
                return cap.read()
            return False, None

    def release(self, index=None):
        if index is None:
            with self.caps_lock:
                indices = list(self.caps.keys())
            for i in indices:
                self.release(i)
        else:
            lock = self._get_cam_lock(index)
            with lock:
                with self.caps_lock:
                    cap = self.caps.pop(index, None)
                if cap:
                    cap.release()
