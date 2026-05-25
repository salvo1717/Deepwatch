class Theme:
    # Palette "Dark Mode Premium"
    BG = "#0D1117"          # GitHub Dark BG
    SURFACE = "#161B22"     # GitHub Dark Surface
    ACCENT = "#2F81F7"      # Blue Accent
    ERROR = "#F85149"       # Red
    SUCCESS = "#3FB950"     # Green
    WARNING = "#D29922"     # Orange/Yellow
    TEXT_PRIMARY = "#C9D1D9"
    TEXT_SECONDARY = "#8B949E"
    BORDER = "#30363D"

    @staticmethod
    def get_sidebar_style():
        return f"""
            QFrame#sidebar {{
                background-color: {Theme.SURFACE};
                border-right: 1px solid {Theme.BORDER};
            }}
            QLabel#logo {{
                color: {Theme.ACCENT};
                font-size: 22px;
                font-weight: bold;
                padding: 20px;
            }}
            QPushButton {{
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 5px;
                color: {Theme.TEXT_PRIMARY};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.BORDER};
            }}
            QPushButton#active_nav {{
                background-color: rgba(47, 129, 247, 0.1);
                color: {Theme.ACCENT};
            }}
        """

    @staticmethod
    def get_main_style():
        return f"""
            QMainWindow, QWidget#main_content {{
                background-color: {Theme.BG};
            }}
            QLabel#header {{
                color: white;
                font-size: 28px;
                font-weight: bold;
            }}
            QFrame#glass_card {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 15px;
            }}
        """
