from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton)
from PyQt6.QtCore import pyqtSignal, Qt
from ..theme import Theme
from ..components import ModernButton, ModernTextField, GlassCard

class RegisterView(QWidget):
    register_success = pyqtSignal()
    go_back = pyqtSignal()
    
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
        
        self.card = GlassCard()
        self.card.setFixedWidth(450)
        
        title = QLabel("CREA NUOVO ACCOUNT")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.card.layout.addWidget(title)
        
        self.user_input = ModernTextField("Scegli Username")
        self.pass_input = ModernTextField("Password", password=True)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {Theme.ERROR}; font-size: 13px;")
        self.error_label.hide()
        
        self.btn_reg = ModernButton("Crea Account")
        self.btn_reg.clicked.connect(self.handle_register)
        
        self.btn_back = QPushButton("Torna al Login")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(f"background: transparent; color: {Theme.TEXT_SECONDARY}; border: none; margin-top: 10px;")
        self.btn_back.clicked.connect(self.go_back.emit)
        
        self.card.layout.addWidget(self.user_input)
        self.card.layout.addWidget(self.pass_input)
        self.card.layout.addWidget(self.error_label)
        self.card.layout.addSpacing(10)
        self.card.layout.addWidget(self.btn_reg)
        self.card.layout.addWidget(self.btn_back, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.content_layout.addWidget(self.card)
        self.master_layout.addWidget(self.content_container)

    def handle_register(self):
        user = self.user_input.text()
        pw = self.pass_input.text()
        
        if not user or not pw:
            self.error_label.setText("❌ Username e Password obbligatori")
            self.error_label.show()
            return
            
        success, message = self.db_manager.register_user(user, pw)
        if success:
            self.register_success.emit()
        else:
            self.error_label.setText(f"❌ {message}")
            self.error_label.show()
