import sys
from GUI.MainWindow import MainWindow
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler

def suppress_qt_warnings(msg_type, msg_log_context, msg_string):
    """Suppress QPainter warnings that occur with matplotlib/Qt interactions."""
    if "QPainter" in msg_string:
        return  # Suppress these warnings
    # Let other messages through
    return

if __name__ == "__main__":
    # Install our custom message handler
    qInstallMessageHandler(suppress_qt_warnings)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())