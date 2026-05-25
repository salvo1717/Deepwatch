import time
import threading
from collections import Counter
from PyQt6.QtCore import QThread, pyqtSignal
from src.utils.image_processing import applica_visione_notturna

class VideoThread(QThread):
    new_frame_signal = pyqtSignal(object)

    def __init__(self, camera_manager, camera_index, detector, db_manager):
        super().__init__()
        self.camera = camera_manager
        self.camera_index = camera_index
        self.detector = detector
        self.db_manager = db_manager
        self.running = True
        self.is_monitoring = False
        self.is_night_mode = False
        self.is_active_view = False # True se la camera è attualmente visualizzata nella UI
        self.last_log_time = 0
        self.last_logged_labels = set()
        self.label_buffer = [] 
        self.buffer_size = 10
        self.min_occurrences = 5

    def run(self):
        print(f"📹 Thread avviato per camera {self.camera_index}")
        while self.running:
            # Sincronizza lo stato di monitoraggio specifico per questa camera
            self.is_monitoring = self.camera.get_monitoring(self.camera_index)
            
            # Se la camera non è visualizzata e non è in monitoraggio, dormi e riprova
            if not self.is_monitoring and not self.is_active_view:
                self.msleep(500)
                continue

            ret, frame = self.camera.read(self.camera_index)
            
            if ret and frame is not None:
                if self.is_night_mode:
                    frame = applica_visione_notturna(frame)
                
                try:
                    # Esegue il rilevamento
                    results = self.detector.predict(frame)
                    
                    if results:
                        current_frame_labels = {self.detector.model.names[int(box.cls)] for box in results[0].boxes}
                        
                        if self.is_monitoring:
                            self.label_buffer.append(current_frame_labels)
                            if len(self.label_buffer) > self.buffer_size:
                                self.label_buffer.pop(0)
                            
                            all_detected = []
                            for s in self.label_buffer: all_detected.extend(list(s))
                            
                            stable_labels = set()
                            if all_detected:
                                counts = Counter(all_detected)
                                stable_labels = {label for label, count in counts.items() if count >= self.min_occurrences}
                            
                            current_time = time.time()
                            should_log = False
                            
                            if stable_labels and stable_labels != self.last_logged_labels:
                                should_log = True
                            elif stable_labels and current_time - self.last_log_time >= 60.0:
                                should_log = True
                                
                            if should_log:
                                detections = [{"label": c, "confidence": float(b.conf)} for b in results[0].boxes if (c := self.detector.model.names[int(b.cls)]) in stable_labels]
                                if detections:
                                    self.db_manager.log_detection(self.camera.get_camera_name(self.camera_index), detections, frame=frame)
                                    self.last_log_time = current_time
                                    self.last_logged_labels = stable_labels
                        else:
                            self.label_buffer.clear()
                        
                        # Disegna i box ed emette il segnale solo se la camera è visualizzata
                        if self.is_active_view:
                            frame = results[0].plot()
                    
                    # Emette il segnale se attiva (fuori dal check results per fluidità)
                    if self.is_active_view:
                        self.new_frame_signal.emit(frame)

                except Exception as e:
                    print(f"IA Error (Cam {self.camera_index}): {e}")
            else:
                self.msleep(100)
            
            # GESTIONE RISORSE:
            if not self.is_active_view:
                self.msleep(200) # Circa 5 FPS per il monitoraggio background
            else:
                self.msleep(10) # Delay minimo per non saturare la CPU
        
        print(f"🛑 Thread fermato per camera {self.camera_index}")

    def stop(self):
        self.running = False
        self.wait()
