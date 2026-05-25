from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from ..theme import Theme
from ..components import ModernButton, ModernTextField, GlassCard

class LoginView(QWidget):
    login_success = pyqtSignal(dict)
    register_requested = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        self.master_layout = QVBoxLayout(self)
        self.master_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.setSpacing(0)
        
        self.logo = QLabel("DEEPWATCH")
        self.logo.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 60px; font-weight: bold; margin-bottom: 30px;")
        self.content_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.card = GlassCard()
        self.card.setFixedWidth(450)
        
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(15)
        
        title = QLabel("ACCEDI AL SISTEMA")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        inner_layout.addWidget(title)
        
        self.user_input = ModernTextField("Nome Utente")
        self.pass_input = ModernTextField("Password", password=True)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {Theme.ERROR}; font-size: 13px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        
        self.submit_btn = ModernButton("Accedi al Sistema")
        self.submit_btn.clicked.connect(self.handle_login)
        
        inner_layout.addWidget(self.user_input)
        inner_layout.addWidget(self.pass_input)
        inner_layout.addWidget(self.error_label)
        inner_layout.addSpacing(10)
        inner_layout.addWidget(self.submit_btn)
        
        self.card.layout.addLayout(inner_layout)
        self.content_layout.addWidget(self.card)
        
        self.register_btn = QPushButton("Non hai un account? Registrati ora")
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.setStyleSheet(f"background: transparent; color: {Theme.TEXT_SECONDARY}; text-decoration: underline; font-size: 14px; border: none; margin-top: 30px;")
        self.register_btn.clicked.connect(self.register_requested.emit)
        self.content_layout.addWidget(self.register_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.master_layout.addWidget(self.content_container)
        
        self.anim = QPropertyAnimation(self.content_container, b"pos")
        QTimer.singleShot(100, self.start_entry_animation)

    def start_entry_animation(self):
        curr_pos = self.content_container.pos()
        target_y = curr_pos.y()
        self.anim.setDuration(800)
        self.anim.setStartValue(QPoint(curr_pos.x(), self.height()))
        self.anim.setEndValue(QPoint(curr_pos.x(), target_y))
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()

    def handle_login(self):
        user = self.user_input.text()
        pw = self.pass_input.text()
        
        if not user or not pw:
            self.error_label.setText("❌ Inserisci tutti i campi")
            self.error_label.show()
            return
            
        success, result = self.db_manager.authenticate(user, pw)
        if success:
            self.login_success.emit(result)
        else:
            self.error_label.setText(f"❌ {result}")
            self.error_label.show()
