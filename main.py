import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
import ctypes
import platform
import threading
import time
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QSystemTrayIcon, QStyle
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QObject
from qt_material import apply_stylesheet
from dotenv import load_dotenv

from src.core.detector import Detector
from src.core.camera import Camera
from src.core.video_thread import VideoThread
from src.utils.database_manager import DatabaseManager
from src.ui.views import LoginView, DashboardView, LiveView, RegisterView, LogsView
from src.ui.theme import Theme

load_dotenv()

def global_exception_handler(exctype, value, tb):
    """Cattura qualsiasi errore fatale e lo scrive su un file di log."""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    with open("crash_report.txt", "w") as f:
        f.write(error_msg)
    print(f"❌ CRASH RILEVATO: {error_msg}")
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_handler

class CameraSwitchWorker(QObject):
    """Gestore asincrono per il cambio camera per non bloccare la UI."""
    finished = pyqtSignal(int, object)
    error = pyqtSignal(int)

    def __init__(self, camera_manager, detector, db_manager, video_threads):
        super().__init__()
        self.camera_manager = camera_manager
        self.detector = detector
        self.db_manager = db_manager
        self.video_threads = video_threads

    def run_switch(self, index):
        try:
            # Operazione hardware lenta
            if index not in self.video_threads:
                self.camera_manager.set_camera(index)
                thread = VideoThread(self.camera_manager, index, self.detector, self.db_manager)
                thread.start()
                self.video_threads[index] = thread
            
            self.finished.emit(index, self.video_threads[index])
        except Exception as e:
            print(f"Hardware Error: {e}")
            self.error.emit(index)

class SentinelApp(QMainWindow):
    notification_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DEEPWATCH - AI Security")
        self.setMinimumSize(1200, 800)
        
        # Tray Icon per Notifiche
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray_icon.show()
        
        self.notification_signal.connect(self.show_notification)
        
        # Hardware & Data
        if platform.system() == "Windows":
            ctypes.windll.ole32.CoInitialize(None)
            
        self.db_manager = DatabaseManager(os.getenv("MONGODB_URI"))
        self.detector = None
        self.camera = Camera(0)

        # Caricamento AI in background per non bloccare la UI all'avvio
        threading.Thread(target=self._init_detector, daemon=True).start()

        # Mappa dei thread attivi per camera {index: VideoThread}
        self.video_threads = {}
        self.is_switching = False

        # UI Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_views()

    def _init_detector(self):
        """Inizializza il motore AI in un thread separato."""
        try:
            from src.core.detector import Detector
            self.detector = Detector()
        except Exception as e:
            print(f"Errore inizializzazione AI: {e}")

    def show_notification(self, title, message):
        """Visualizza una notifica di sistema tramite tray icon."""
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Warning,
            5000 # 5 secondi
        )

    def _get_or_create_thread(self, index):
        """Metodo sincrono (usato solo all'avvio o in show_live)."""
        # Assicuriamoci che il detector sia pronto
        if self.detector is None:
            from src.core.detector import Detector
            self.detector = Detector()

        if index not in self.video_threads:
            self.camera.set_camera(index)
            thread = VideoThread(self.camera, index, self.detector, self.db_manager)
            # Collega il segnale di notifica del thread a quello dell'app
            thread.notification_requested.connect(self.notification_signal.emit)
            self.video_threads[index] = thread
            thread.start()
        return self.video_threads[index]

    def _start_monitored_cameras(self):
        available = self.camera.get_available_cameras()
        for cam in available:
            idx = cam['index']
            if self.camera.get_monitoring(idx):
                self._get_or_create_thread(idx)

    def _stop_unnecessary_threads(self):
        current_view_idx = self.camera.current_index if self.stack.currentWidget() == getattr(self, 'live_view', None) else -1
        for idx in list(self.video_threads.keys()):
            if not self.camera.get_monitoring(idx) and idx != current_view_idx:
                thread = self.video_threads.pop(idx)
                thread.stop()
                self.camera.release(idx)

    def init_views(self):
        self.login_view = LoginView(self.db_manager)
        self.login_view.login_success.connect(self.show_dashboard)
        self.login_view.register_requested.connect(self.show_registration)
        self.stack.addWidget(self.login_view)
        
        self.reg_view = RegisterView(self.db_manager)
        self.reg_view.go_back.connect(lambda: self.stack.setCurrentWidget(self.login_view))
        self.reg_view.register_success.connect(lambda: self.stack.setCurrentWidget(self.login_view))
        self.stack.addWidget(self.reg_view)

        self.logs_view = LogsView(self.db_manager)
        self.logs_view.go_back.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))
        self.stack.addWidget(self.logs_view)
        
        self.stack.setCurrentWidget(self.login_view)

    def show_registration(self):
        self.stack.setCurrentWidget(self.reg_view)

    def show_dashboard(self, user_data):
        self.dashboard_view = DashboardView(user_data, self.db_manager)
        self.dashboard_view.go_live.connect(self.show_live)
        self.dashboard_view.go_logs.connect(self.show_logs)
        self.stack.addWidget(self.dashboard_view)
        self.stack.setCurrentWidget(self.dashboard_view)
        self._start_monitored_cameras()
        self._stop_unnecessary_threads()

    def show_logs(self):
        self.logs_view.load_logs()
        self.stack.setCurrentWidget(self.logs_view)

    def show_live(self):
        if hasattr(self, 'live_view') and self.live_view is not None:
            old_idx = self.camera.current_index
            if old_idx in self.video_threads:
                self.video_threads[old_idx].is_active_view = False
                try: self.video_threads[old_idx].new_frame_signal.disconnect(self.process_frame)
                except: pass
            self.stack.removeWidget(self.live_view)
            self.live_view.deleteLater()
            
        self.live_view = LiveView(self.camera, self.detector)
        self.live_view.go_back.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))
        self.live_view.camera_changed.connect(self.change_camera)
        self.live_view.toggle_monitoring.connect(self.update_monitoring_status)
        self.live_view.toggle_night_mode.connect(self.update_night_mode_status)
        
        idx = self.camera.current_index
        self.live_view.is_monitoring = self.camera.get_monitoring(idx)
        self.live_view.sync_ui_to_monitoring_state()
        
        thread = self._get_or_create_thread(idx)
        thread.is_active_view = True
        thread.new_frame_signal.connect(self.process_frame)
        
        self.stack.addWidget(self.live_view)
        self.stack.setCurrentWidget(self.live_view)

    def update_monitoring_status(self, active):
        idx = self.camera.current_index
        self.camera.set_monitoring(idx, active)
        if active: self._get_or_create_thread(idx)

    def update_night_mode_status(self, active):
        idx = self.camera.current_index
        if idx in self.video_threads:
            self.video_threads[idx].is_night_mode = active

    def change_camera(self, index):
        """Cambia la camera visualizzata gestendo correttamente lo stato asincrono."""
        if self.is_switching or index == self.camera.current_index:
            return

        self.is_switching = True
        old_idx = self.camera.current_index

        if hasattr(self, 'live_view'):
            self.live_view.cam_select.setEnabled(False)
            self.live_view.status_label.setText("⌛ CAMBIO IN CORSO...")
            self.live_view.video_label.setText("CARICAMENTO...")

        # Downgrade immediato vecchio thread
        if old_idx in self.video_threads:
            self.video_threads[old_idx].is_active_view = False
            try: self.video_threads[old_idx].new_frame_signal.disconnect(self.process_frame)
            except: pass

        def _bg_task():
            worker = CameraSwitchWorker(self.camera, self.detector, self.db_manager, self.video_threads)
            # Incolla i risultati alla UI
            worker.finished.connect(self._on_switch_complete)
            worker.error.connect(self._on_switch_error)
            worker.run_switch(index)
            
            # Cleanup vecchio (in background totale)
            if old_idx in self.video_threads and not self.camera.get_monitoring(old_idx):
                old_t = self.video_threads.pop(old_idx, None)
                if old_t:
                    old_t.stop()
                    self.camera.release(old_idx)

        threading.Thread(target=_bg_task, daemon=True).start()

    def _on_switch_complete(self, index, thread):
        self.camera.current_index = index
        self.is_switching = False
        
        # Disconnetti eventuali altri rimasti (sicurezza)
        for tidx, t in self.video_threads.items():
            if tidx != index:
                try: t.new_frame_signal.disconnect(self.process_frame)
                except: pass

        thread.is_active_view = True
        thread.new_frame_signal.connect(self.process_frame)
        # Assicura connessione notifica (nel caso sia stato creato asincronamente)
        try: thread.notification_requested.connect(self.notification_signal.emit, Qt.ConnectionType.UniqueConnection)
        except: pass
        
        if hasattr(self, 'live_view'):
            self.live_view.cam_select.setEnabled(True)
            self.live_view.is_monitoring = self.camera.get_monitoring(index)
            self.live_view.sync_ui_to_monitoring_state()

    def _on_switch_error(self, index):
        self.is_switching = False
        if hasattr(self, 'live_view'):
            self.live_view.cam_select.setEnabled(True)
            self.live_view.status_label.setText("❌ ERRORE HARDWARE")

    def process_frame(self, frame):
        if self.stack.currentWidget() == getattr(self, 'live_view', None):
            self.live_view.update_frame(frame)

    def closeEvent(self, event):
        for thread in self.video_threads.values():
            thread.stop()
        self.camera.release()
        self.db_manager.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml')
    app.setStyleSheet(app.styleSheet() + Theme.get_sidebar_style() + Theme.get_main_style())
    window = SentinelApp()
    window.show()
    sys.exit(app.exec())
