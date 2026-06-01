import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QFileDialog, QHeaderView, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
from database import SourceDocument, get_db_session

class SourceLibraryTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Local document storage directory
        self.doc_storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "documents")
        if not os.path.exists(self.doc_storage_dir):
            os.makedirs(self.doc_storage_dir)

        self.layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("<h2>Source Library Management</h2>")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(header_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_upload_doc = QPushButton("Upload Document (.pdf, .xlsx, etc.)")
        self.btn_upload_doc.clicked.connect(self.upload_document)
        button_layout.addWidget(self.btn_upload_doc)
        
        self.btn_add_link = QPushButton("Add Web Source Link")
        self.btn_add_link.clicked.connect(self.add_web_link)
        button_layout.addWidget(self.btn_add_link)
        
        self.btn_refresh = QPushButton("Refresh Library")
        self.btn_refresh.clicked.connect(self.load_sources)
        button_layout.addWidget(self.btn_refresh)
        
        self.layout.addLayout(button_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Active Content", "Delete"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)
        
        self.load_sources()
        
    def load_sources(self):
        """Loads sources from the SQLite database into the table."""
        session = get_db_session()
        sources = session.query(SourceDocument).all()
        
        self.table.setRowCount(len(sources))
        
        for row, source in enumerate(sources):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(source.id)))
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(source.name))
            
            # Type
            self.table.setItem(row, 2, QTableWidgetItem(source.source_type.upper()))
            
            # Active Toggle Button
            toggle_btn = QPushButton("Active" if source.is_active else "Inactive")
            toggle_btn.setCheckable(True)
            toggle_btn.setChecked(source.is_active)
            toggle_btn.clicked.connect(lambda checked, s_id=source.id: self.toggle_source_active(s_id, checked))
            self.table.setCellWidget(row, 3, toggle_btn)
            
            # Delete Button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, s_id=source.id: self.delete_source(s_id))
            self.table.setCellWidget(row, 4, delete_btn)
            
        session.close()

    def toggle_source_active(self, source_id, is_active):
        session = get_db_session()
        source = session.query(SourceDocument).filter_by(id=source_id).first()
        if source:
            source.is_active = is_active
            session.commit()
        session.close()
        self.load_sources()

    def delete_source(self, source_id):
        reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete this source?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            session = get_db_session()
            source = session.query(SourceDocument).filter_by(id=source_id).first()
            if source:
                # Remove file if it's a local document
                if source.file_path and os.path.exists(source.file_path):
                    try:
                        os.remove(source.file_path)
                    except Exception as e:
                        print(f"Error removing file: {e}")
                
                session.delete(source)
                session.commit()
            session.close()
            self.load_sources()

    def upload_document(self):
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, "Select Documents to Upload", 
            "", 
            "Documents (*.pdf *.xlsx *.xls *.csv *.docx *.txt)"
        )
        
        if file_paths:
            session = get_db_session()
            for path in file_paths:
                file_name = os.path.basename(path)
                file_ext = os.path.splitext(file_name)[1].lower().strip('.')
                
                # Copy file to local storage
                dest_path = os.path.join(self.doc_storage_dir, file_name)
                
                # Handle duplicate filenames
                counter = 1
                while os.path.exists(dest_path):
                    name, ext = os.path.splitext(file_name)
                    dest_path = os.path.join(self.doc_storage_dir, f"{name}_{counter}{ext}")
                    counter += 1
                    
                shutil.copy2(path, dest_path)
                
                # Add to DB
                new_source = SourceDocument(
                    name=os.path.basename(dest_path),
                    file_path=dest_path,
                    source_type=file_ext,
                    is_active=True
                )
                session.add(new_source)
                
            session.commit()
            session.close()
            self.load_sources()

    def add_web_link(self):
        url, ok = QInputDialog.getText(self, "Add Web Source Link", "Enter URL (e.g., https://example.com/guidelines):")
        if ok and url:
            name, ok_name = QInputDialog.getText(self, "Web Source Name", "Enter a name for this source:")
            if ok_name and name:
                session = get_db_session()
                new_source = SourceDocument(
                    name=name,
                    url=url,
                    source_type="link",
                    is_active=True
                )
                session.add(new_source)
                session.commit()
                session.close()
                self.load_sources()
