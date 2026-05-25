import platform
from plyer import notification

def send_desktop_notification(title, message):
    """Invia una notifica di sistema (Windows/Linux/macOS)."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="DEEPWATCH",
            timeout=10 # Secondi di permanenza
        )
    except Exception as e:
        print(f"⚠️ Errore invio notifica: {e}")
