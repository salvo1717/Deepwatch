from PyQt6.QtWidgets import (QPushButton, QLineEdit, QFrame, QVBoxLayout, 
                             QLabel, QHBoxLayout, QGraphicsDropShadowEffect, QWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QIcon
from .theme import Theme

class ModernButton(QPushButton):
    def __init__(self, text, color=Theme.ACCENT):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(45)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                padding: 0 15px;
            }}
            QPushButton:hover {{ background-color: {color}dd; }}
            QPushButton:pressed {{ background-color: {color}aa; }}
        """)

class ModernTextField(QFrame):
    def __init__(self, placeholder, password=False):
        super().__init__()
        self.setFixedHeight(50)
        self.password_mode = password
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
            }}
            QFrame:focus-within {{ border: 1px solid {Theme.ACCENT}; background-color: rgba(255, 255, 255, 0.08); }}
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 10, 0)
        self.layout.setSpacing(5)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("background: transparent; border: none; color: white; font-size: 15px; selection-background-color: #2F81F7;")
        self.layout.addWidget(self.input)
        
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn = QPushButton("👁")
            self.toggle_btn.setFixedSize(35, 35)
            self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.toggle_btn.setStyleSheet("background: transparent; color: #8B949E; border: none; font-size: 18px;")
            self.toggle_btn.clicked.connect(self.toggle_password)
            self.layout.addWidget(self.toggle_btn)

    def toggle_password(self):
        if self.input.echoMode() == QLineEdit.EchoMode.Password:
            self.input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("🙈")
        else:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("👁")

    def text(self): return self.input.text()
    def setText(self, t): self.input.setText(t)

class GlassCard(QFrame):
    def __init__(self, title=None):
        super().__init__()
        self.setObjectName("glass_card")
        # Ensure no background on the frame itself except via QSS
        self.setStyleSheet(f"""
            QFrame#glass_card {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 15px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        if title and title.strip():
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet(f"color: white; font-size: 20px; font-weight: bold; background: transparent; border: none;")
            self.layout.addWidget(self.title_label)
            
            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet(f"background-color: {Theme.BORDER};")
            self.layout.addWidget(line)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

    def add_widget(self, widget):
        self.layout.addWidget(widget)

    def add_layout(self, layout):
        self.layout.addLayout(layout)
