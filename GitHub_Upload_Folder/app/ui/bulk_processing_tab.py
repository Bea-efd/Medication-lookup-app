import os
import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt
from core.engine import LookupEngine

class BulkProcessingTab(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        self.current_df = None
        self.processed_df = None
        
        # Header
        header_label = QLabel("<h2>Bulk Processing (Excel/CSV)</h2>")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(header_label)
        
        instructions = QLabel(
            "Upload an Excel or CSV file containing at least two columns: 'Medication' and 'Dose'.\n"
            "The app will process the list using your active sources and allow you to download the results."
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(instructions)
        
        # Web Search Toggle
        self.web_search_toggle = QCheckBox("Enable Web Search (Include active web links during bulk process)")
        self.web_search_toggle.setChecked(True)
        self.layout.addWidget(self.web_search_toggle)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_upload = QPushButton("Upload File to Process")
        self.btn_upload.clicked.connect(self.upload_file)
        button_layout.addWidget(self.btn_upload)
        
        self.btn_process = QPushButton("Run Lookup Engine")
        self.btn_process.clicked.connect(self.process_data)
        self.btn_process.setEnabled(False)
        button_layout.addWidget(self.btn_process)
        
        self.btn_download = QPushButton("Download Results")
        self.btn_download.clicked.connect(self.download_results)
        self.btn_download.setEnabled(False)
        button_layout.addWidget(self.btn_download)
        
        self.layout.addLayout(button_layout)
        
        # Table Preview
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel or CSV", "", "Spreadsheets (*.xlsx *.xls *.csv)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.current_df = pd.read_csv(file_path)
                else:
                    self.current_df = pd.read_excel(file_path)
                    
                # Check for required columns (case insensitive)
                cols_lower = [str(c).lower().strip() for c in self.current_df.columns]
                
                # Try to identify which columns are medication and dose
                med_col = None
                dose_col = None
                
                for i, col in enumerate(cols_lower):
                    if "med" in col or "name" in col or "drug" in col:
                        med_col = self.current_df.columns[i]
                    if "dose" in col or "strength" in col:
                        dose_col = self.current_df.columns[i]
                        
                if not med_col or not dose_col:
                    QMessageBox.warning(self, "Missing Columns", 
                                        "Could not identify 'Medication' and 'Dose' columns. "
                                        "Please ensure your file has columns with these names.")
                    self.current_df = None
                    return
                
                # Store the identified column names for processing
                self.med_col = med_col
                self.dose_col = dose_col
                
                self.preview_data(self.current_df)
                self.btn_process.setEnabled(True)
                self.btn_download.setEnabled(False)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def preview_data(self, df):
        """Displays the top 50 rows in the UI table."""
        preview_df = df.head(50)
        
        self.table.setColumnCount(len(preview_df.columns))
        self.table.setRowCount(len(preview_df.index))
        self.table.setHorizontalHeaderLabels(preview_df.columns.astype(str))
        
        for i in range(len(preview_df.index)):
            for j in range(len(preview_df.columns)):
                val = str(preview_df.iat[i, j])
                if val == "nan": val = ""
                self.table.setItem(i, j, QTableWidgetItem(val))
                
        self.table.resizeColumnsToContents()

    def process_data(self):
        if self.current_df is None: return
        
        self.btn_process.setEnabled(False)
        self.btn_upload.setEnabled(False)
        
        try:
            # Create a copy to store results
            self.processed_df = self.current_df.copy()
            
            # Initialize engine here so it gets fresh active sources
            engine = LookupEngine()
            
            # Add new columns
            self.processed_df["ATC Codes"] = ""
            self.processed_df["Price"] = ""
            self.processed_df["Formulation"] = ""
            self.processed_df["Active Ingredient"] = ""
            self.processed_df["Packet Size"] = ""
            self.processed_df["Source Citations"] = ""
            
            # Iterate and run lookup
            for index, row in self.current_df.iterrows():
                med = str(row[self.med_col])
                dose = str(row[self.dose_col])
                
                if med != "nan" and dose != "nan":
                    result = engine.search_medication(med, dose, allow_web=self.web_search_toggle.isChecked())
                    
                    self.processed_df.at[index, "ATC Codes"] = result.get("atc_codes", "")
                    
                    all_prices = []
                    all_forms = []
                    all_actives = []
                    all_sizes = []
                    for m in result.get("matches", []):
                        if m.get("price", "Not Found") != "Not Found":  all_prices.append(str(m["price"]))
                        if m.get("formulation", "Not Found") != "Not Found": all_forms.append(str(m["formulation"]))
                        if m.get("active_ingredient", "Not Found") != "Not Found": all_actives.append(str(m["active_ingredient"]))
                        if m.get("packet_size", "Not Found") != "Not Found": all_sizes.append(str(m["packet_size"]))
                        
                    self.processed_df.at[index, "Price"] = " | ".join(all_prices) if all_prices else "Not Found"
                    self.processed_df.at[index, "Formulation"] = " | ".join(all_forms) if all_forms else "Not Found"
                    self.processed_df.at[index, "Active Ingredient"] = " | ".join(all_actives) if all_actives else "Not Found"
                    self.processed_df.at[index, "Packet Size"] = " | ".join(all_sizes) if all_sizes else "Not Found"
                    self.processed_df.at[index, "Source Citations"] = result.get("sources", "")
            
            self.preview_data(self.processed_df)
            QMessageBox.information(self, "Success", "Processing complete!")
            self.btn_download.setEnabled(True)
            
        except Exception as e:
             QMessageBox.critical(self, "Processing Error", f"An error occurred:\n{str(e)}")
             
        finally:
            self.btn_process.setEnabled(True)
            self.btn_upload.setEnabled(True)

    def download_results(self):
        if self.processed_df is None: return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Processed Results", "Processed_Medications.xlsx", "Excel (*.xlsx)"
        )
        
        if file_path:
            try:
                self.processed_df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Saved", f"Results successfully saved to:\n{file_path}")
            except Exception as e:
                 QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")
