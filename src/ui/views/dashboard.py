from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from ..theme import Theme
from ..components import ModernButton, GlassCard

class DashboardView(QWidget):
    go_live = pyqtSignal()
    go_logs = pyqtSignal()
    
    def __init__(self, user_data, db_manager):
        super().__init__()
        self.user_data = user_data
        self.db_manager = db_manager
        self.init_ui()
        
        # Timer per l'aggiornamento automatico (ogni 30 secondi)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(f"background-color: {Theme.SURFACE}; border-right: 1px solid {Theme.BORDER};")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(20, 30, 20, 20)
        
        logo = QLabel("DEEPWATCH")
        logo.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 22px; font-weight: bold;")
        side_layout.addWidget(logo)
        side_layout.addSpacing(30)
        
        btn_dash = ModernButton("Dashboard")
        btn_live = ModernButton("Live Feed")
        btn_live.clicked.connect(self.go_live.emit)
        
        btn_logs = ModernButton("Visual Logs")
        btn_logs.clicked.connect(self.go_logs.emit)
        
        side_layout.addWidget(btn_dash)
        side_layout.addWidget(btn_live)
        side_layout.addWidget(btn_logs)
        side_layout.addStretch()
        
        self.main_layout.addWidget(self.sidebar)
        
        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        header_row = QHBoxLayout()
        welcome = QLabel(f"Bentornato, {self.user_data.get('username', 'Utente')}")
        welcome.setStyleSheet("color: white; font-size: 35px; font-weight: bold;")
        header_row.addWidget(welcome)
        header_row.addStretch()
        
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet(f"color: {Theme.ACCENT}; background: transparent; border: 1px solid {Theme.ACCENT}; border-radius: 8px; padding: 8px 15px; font-weight: bold;")
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)
        
        content_layout.addLayout(header_row)
        content_layout.addSpacing(20)
        
        # Stats Cards
        self.stats_row = QHBoxLayout()
        self.card_total = GlassCard("Totale Rilevamenti")
        self.val_total = QLabel("0")
        self.val_total.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 40px; font-weight: bold;")
        self.card_total.layout.addWidget(self.val_total)
        
        self.card_people = GlassCard("Persone Rilevate")
        self.val_people = QLabel("0")
        self.val_people.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 40px; font-weight: bold;")
        self.card_people.layout.addWidget(self.val_people)
        
        self.card_others = GlassCard("Altri Oggetti")
        self.val_others = QLabel("0")
        self.val_others.setStyleSheet(f"color: #FFA500; font-size: 40px; font-weight: bold;")
        self.card_others.layout.addWidget(self.val_others)
        
        self.stats_row.addWidget(self.card_total)
        self.stats_row.addWidget(self.card_people)
        self.stats_row.addWidget(self.card_others)
        content_layout.addLayout(self.stats_row)
        
        content_layout.addSpacing(30)
        
        # Filtri e Tabella
        filter_label = QLabel("Cronologia Rilevamenti")
        filter_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        content_layout.addWidget(filter_label)
        
        filter_row = QHBoxLayout()
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["Tutti gli oggetti", "Persone", "Altri Oggetti"])
        self.combo_filter.setFixedWidth(200)
        self.combo_filter.setFixedHeight(40)
        self.combo_filter.setStyleSheet(f"background: {Theme.SURFACE}; color: white; border: 1px solid {Theme.BORDER}; border-radius: 5px;")
        self.combo_filter.currentIndexChanged.connect(self.load_table_data)
        
        filter_row.addWidget(self.combo_filter)
        filter_row.addStretch()
        content_layout.addLayout(filter_row)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Data/Ora", "Camera", "Oggetti", "Confidenza Media"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.SURFACE};
                color: white;
                gridline-color: {Theme.BORDER};
                border-radius: 10px;
                border: 1px solid {Theme.BORDER};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG};
                color: {Theme.ACCENT};
                padding: 10px;
                font-weight: bold;
                border: none;
            }}
            QTableWidget::item {{
                padding: 10px;
            }}
        """)
        content_layout.addWidget(self.table)
        
        self.main_layout.addWidget(content)
        
        self.refresh_data()

    def refresh_data(self):
        stats = self.db_manager.get_stats()
        self.val_total.setText(str(stats.get('detections', 0)))
        self.val_people.setText(str(stats.get('people', 0)))
        self.val_others.setText(str(stats.get('others', 0)))
        self.load_table_data()

    def load_table_data(self):
        filter_idx = self.combo_filter.currentIndex()
        class_filter = None
        if filter_idx == 1: class_filter = "person"
        
        detections = self.db_manager.get_detections(limit=50, class_filter=class_filter)
        
        if filter_idx == 2:
            detections = [d for d in detections if any(obj.get('label', obj.get('class')) != 'person' for obj in d.objects)]

        self.table.setRowCount(len(detections))
        for i, det in enumerate(detections):
            # Prova a prendere 'label' (nuovo) o 'class' (vecchio)
            objs_str = ", ".join([f"{obj.get('label', obj.get('class', 'unknown'))}" for obj in det.objects])
            # Prova a prendere 'confidence' (nuovo) o 'conf' (vecchio)
            avg_conf = sum([obj.get('confidence', obj.get('conf', 0)) for obj in det.objects]) / len(det.objects) if det.objects else 0
            
            self.table.setItem(i, 0, QTableWidgetItem(det.timestamp.strftime("%d/%m/%Y %H:%M")))
            self.table.setItem(i, 1, QTableWidgetItem(det.camera))
            self.table.setItem(i, 2, QTableWidgetItem(objs_str))
            self.table.setItem(i, 3, QTableWidgetItem(f"{avg_conf:.2%}"))
