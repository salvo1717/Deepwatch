from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QMessageBox, QDialog)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
import cv2
import base64
import numpy as np
from ..theme import Theme
from ..components import ModernButton, GlassCard

class LogDetailDialog(QDialog):
    """Dialogo per visualizzare un log in dettaglio con immagine grande."""
    def __init__(self, detection, parent=None):
        super().__init__(parent)
        self.det = detection
        self.setWindowTitle(f"Dettaglio Rilevamento - {self.det.timestamp.strftime('%H:%M:%S')}")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(f"background-color: {Theme.SURFACE}; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Immagine Grande
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background: black; border-radius: 10px; border: 1px solid #444;")
        
        if self.det.image:
            try:
                img_data = base64.b64decode(self.det.image)
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_img)
                self.img_label.setPixmap(pixmap.scaled(1200, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            except:
                self.img_label.setText("⚠️ Errore decodifica immagine")
        else:
            self.img_label.setText("📷 Nessuna immagine catturata")
            
        layout.addWidget(self.img_label, 1)
        
        # Info Pannello
        info_panel = QFrame()
        info_panel.setStyleSheet(f"background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px;")
        info_layout = QHBoxLayout(info_panel)
        
        text_layout = QVBoxLayout()
        title = QLabel(f"📅 {self.det.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
        title.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 22px; font-weight: bold;")
        
        cam = QLabel(f"📷 Telecamera: {self.det.camera}")
        cam.setStyleSheet("font-size: 16px;")
        
        objs_str = ", ".join([f"{o.get('label', '??')} ({o.get('confidence', 0):.1%})" for o in self.det.objects])
        objs = QLabel(f"🔍 Oggetti: {objs_str}")
        objs.setStyleSheet("font-size: 16px; color: #BBB;")
        
        text_layout.addWidget(title)
        text_layout.addWidget(cam)
        text_layout.addWidget(objs)
        info_layout.addLayout(text_layout)
        
        btn_close = ModernButton("Chiudi", Theme.BORDER)
        btn_close.setFixedWidth(150)
        btn_close.clicked.connect(self.accept)
        info_layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(info_panel)

class LogsView(QWidget):
    go_back = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
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
        
        side_layout.addSpacing(20)
        
        self.btn_clear = ModernButton("Elimina tutti i Log", Theme.ERROR)
        self.btn_clear.clicked.connect(self.handle_clear_logs)
        side_layout.addWidget(self.btn_clear)
        
        side_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)
        
        # Content
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("🖼️ VISUAL DETECTION LOGS")
        header.setStyleSheet("color: white; font-size: 28px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.logs_layout = QVBoxLayout(self.scroll_content)
        self.logs_layout.setSpacing(20)
        self.logs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        
        layout.addWidget(self.scroll)
        self.main_layout.addWidget(content)

    def handle_clear_logs(self):
        confirm = QMessageBox.question(
            self, "Conferma Eliminazione",
            "Sei sicuro di voler eliminare permanentemente TUTTI i log?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.db_manager.clear_all_logs()
            if success:
                QMessageBox.information(self, "Successo", message)
                self.load_logs()
            else:
                QMessageBox.critical(self, "Errore", f"Impossibile eliminare i log: {message}")

    def handle_delete_log(self, log_id):
        confirm = QMessageBox.question(
            self, "Conferma Eliminazione",
            "Vuoi eliminare questo log specifico?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.db_manager.delete_log(log_id)
            if success:
                self.load_logs()
            else:
                QMessageBox.critical(self, "Errore", f"Errore durante l'eliminazione: {message}")

    def show_detail(self, det):
        dialog = LogDetailDialog(det, self)
        dialog.exec()

    def load_logs(self):
        # Svuota layout precedente
        while self.logs_layout.count():
            child = self.logs_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        detections = self.db_manager.get_detections(limit=30)
        
        if not detections:
            empty_lbl = QLabel("Nessun log trovato nel database.")
            empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 18px; margin-top: 50px;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.logs_layout.addWidget(empty_lbl)
            return

        for det in detections:
            card = GlassCard()
            card.setFixedHeight(250)
            h_row = QHBoxLayout()
            
            # Immagine (miniante)
            img_label = QLabel()
            img_label.setFixedSize(300, 200)
            img_label.setStyleSheet("background: black; border-radius: 10px;")
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if det.image:
                try:
                    img_data = base64.b64decode(det.image)
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_img)
                    img_label.setPixmap(pixmap.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio))
                except:
                    img_label.setText("🖼️ Immagine Corrotta")
            else:
                img_label.setText("📷 No Capture")
                
            # Info
            info_layout = QVBoxLayout()
            time_lbl = QLabel(f"📅 {det.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
            time_lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 18px; font-weight: bold;")
            
            cam_lbl = QLabel(f"📷 Camera: {det.camera}")
            cam_lbl.setStyleSheet("color: white; font-size: 15px;")
            
            objs_str = ", ".join([obj.get('label', 'unknown') for obj in det.objects])
            objs_lbl = QLabel(f"🔍 Rilevati: {objs_str}")
            objs_lbl.setStyleSheet("color: #AAA; font-size: 14px;")
            
            # Bottoni
            btn_layout = QHBoxLayout()
            
            btn_view = ModernButton("Visualizza", Theme.ACCENT)
            btn_view.setFixedWidth(120)
            btn_view.setFixedHeight(35)
            btn_view.clicked.connect(lambda checked, d=det: self.show_detail(d))
            
            btn_del = ModernButton("Elimina", Theme.ERROR)
            btn_del.setFixedWidth(120)
            btn_del.setFixedHeight(35)
            btn_del.clicked.connect(lambda checked, lid=det.id: self.handle_delete_log(lid))
            
            btn_layout.addWidget(btn_view)
            btn_layout.addWidget(btn_del)
            btn_layout.addStretch()
            
            info_layout.addWidget(time_lbl)
            info_layout.addWidget(cam_lbl)
            info_layout.addWidget(objs_lbl)
            info_layout.addStretch()
            info_layout.addLayout(btn_layout)
            
            h_row.addWidget(img_label)
            h_row.addLayout(info_layout, 1)
            card.layout.addLayout(h_row)
            
            self.logs_layout.addWidget(card)
