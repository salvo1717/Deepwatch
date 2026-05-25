from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
from ..theme import Theme
from ..components import ModernButton, GlassCard

class LiveView(QWidget):
    go_back = pyqtSignal()
    camera_changed = pyqtSignal(int)
    toggle_monitoring = pyqtSignal(bool)
    toggle_night_mode = pyqtSignal(bool)
    
    def __init__(self, camera, detector):
        super().__init__()
        self.camera = camera
        self.detector = detector
        self.is_monitoring = False
        self.is_night_mode = False
        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(f"background-color: {Theme.SURFACE}; border-right: 1px solid {Theme.BORDER};")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(20, 30, 20, 20)
        
        btn_back = ModernButton("Torna alla Home", Theme.BORDER)
        btn_back.clicked.connect(self.go_back.emit)
        side_layout.addWidget(btn_back)
        
        side_layout.addSpacing(30)
        
        # Controls Section
        control_label = QLabel("CONTROLLI")
        control_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold; font-size: 12px;")
        side_layout.addWidget(control_label)
        
        self.btn_monitor = ModernButton("Avvia Monitoraggio", "#555555")
        self.btn_monitor.clicked.connect(self.handle_monitor_toggle)
        side_layout.addWidget(self.btn_monitor)
        
        self.btn_night = ModernButton("Visione Notturna: OFF", "#555555")
        self.btn_night.clicked.connect(self.handle_night_toggle)
        side_layout.addWidget(self.btn_night)
        
        side_layout.addStretch()
        
        # Status Card
        self.status_card = GlassCard()
        self.status_card.setFixedHeight(100)
        self.status_label = QLabel("SISTEMA PRONTO")
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold;")
        self.status_card.layout.addWidget(self.status_label)
        side_layout.addWidget(self.status_card)
        
        self.main_layout.addWidget(self.sidebar)
        
        # Main
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header_row = QHBoxLayout()
        header = QLabel("🔴 LIVE FEED")
        header.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        
        # Camera Selector
        self.cam_select = QComboBox()
        self.cam_select.setFixedWidth(300)
        self.cam_select.setFixedHeight(40)
        self.cam_select.setStyleSheet(f"""
            QComboBox {{ 
                background: {Theme.SURFACE}; color: white; border: 1px solid {Theme.BORDER}; 
                border-radius: 8px; padding-left: 10px; font-weight: bold;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background: {Theme.BG}; color: white; selection-background-color: {Theme.ACCENT}; }}
        """)
        
        # Forza scansione all'apertura della vista
        cameras = self.camera.get_available_cameras(force_scan=True)
        current_cam_idx = self.camera.current_index
        default_index = 0
        
        for i, c in enumerate(cameras):
            self.cam_select.addItem(f"📷 {c['name']}", c['index'])
            if c['index'] == current_cam_idx:
                default_index = i
            
        self.cam_select.setCurrentIndex(default_index)
        self.cam_select.currentIndexChanged.connect(self.on_cam_index_change)
        
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(self.cam_select)
        layout.addLayout(header_row)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; border-radius: 20px; border: 2px solid #2F81F7;")
        layout.addWidget(self.video_label, 1)
        
        self.main_layout.addWidget(content)

    def handle_monitor_toggle(self):
        self.is_monitoring = not self.is_monitoring
        self.sync_ui_to_monitoring_state()
        self.toggle_monitoring.emit(self.is_monitoring)

    def sync_ui_to_monitoring_state(self):
        """Aggiorna l'aspetto dei pulsanti in base allo stato attuale."""
        if self.is_monitoring:
            self.btn_monitor.setText("Ferma Monitoraggio")
            self.btn_monitor.setStyleSheet(self.btn_monitor.styleSheet().replace("#555555", Theme.ERROR).replace(Theme.ERROR, Theme.ERROR))
            self.status_label.setText("🔴 MONITORAGGIO ATTIVO")
            self.status_label.setStyleSheet(f"color: {Theme.ERROR}; font-weight: bold;")
        else:
            self.btn_monitor.setText("Avvia Monitoraggio")
            self.btn_monitor.setStyleSheet(self.btn_monitor.styleSheet().replace(Theme.ERROR, "#555555").replace("#555555", "#555555"))
            self.status_label.setText("SISTEMA PRONTO")
            self.status_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold;")

    def handle_night_toggle(self):
        self.is_night_mode = not self.is_night_mode
        if self.is_night_mode:
            self.btn_night.setText("Visione Notturna: ON")
            self.btn_night.setStyleSheet(self.btn_night.styleSheet().replace("#555555", Theme.SUCCESS))
        else:
            self.btn_night.setText("Visione Notturna: OFF")
            self.btn_night.setStyleSheet(self.btn_night.styleSheet().replace(Theme.SUCCESS, "#555555"))
        
        self.toggle_night_mode.emit(self.is_night_mode)

    def on_cam_index_change(self, index):
        cam_idx = self.cam_select.currentData()
        # Emetti solo se l'indice è diverso da quello attuale hardware
        if cam_idx != self.camera.current_index:
            self.camera_changed.emit(cam_idx)

    def update_frame(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        if not self.video_label.size().isEmpty():
            scaled = pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.video_label.setPixmap(scaled)
