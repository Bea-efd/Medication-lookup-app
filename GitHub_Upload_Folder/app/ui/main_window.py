from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QStatusBar
)
from PySide6.QtCore import Qt
from ui.source_library_tab import SourceLibraryTab
from ui.single_lookup_tab import SingleLookupTab
from ui.bulk_processing_tab import BulkProcessingTab

class MainWindow(QMainWindow):
    def __init__(self, client_mode=False):
        super().__init__()
        
        self.setWindowTitle("Medication Lookup App")
        self.setMinimumSize(900, 600)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Setup Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create different tabs
        self.setup_single_lookup_tab()
        self.setup_bulk_processing_tab()
        
        if not client_mode:
            self.setup_source_library_tab()
        
        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")
        
    def setup_single_lookup_tab(self):
        tab = SingleLookupTab()
        self.tabs.addTab(tab, "Single Lookup")
        
    def setup_bulk_processing_tab(self):
        tab = BulkProcessingTab()
        self.tabs.addTab(tab, "Bulk Processing")

    def setup_source_library_tab(self):
        tab = SourceLibraryTab()
        self.tabs.addTab(tab, "Source Library")
