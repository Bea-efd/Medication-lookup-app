import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("MedicationLookupClient")
    app.setOrganizationName("MedicationLookupApp")
    
    # Create and show the main window in Client Mode (hides the library tab)
    window = MainWindow(client_mode=True)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
