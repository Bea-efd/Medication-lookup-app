from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QLabel, QTextBrowser, QCheckBox
)
from PySide6.QtCore import Qt
from core.engine import LookupEngine

class SingleLookupTab(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("<h2>Single Medication Lookup</h2>")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(header_label)
        
        # Form
        form_layout = QFormLayout()
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g., Paracetamol")
        form_layout.addRow("Medication Name:", self.input_name)
        
        self.input_dose = QLineEdit()
        self.input_dose.setPlaceholderText("e.g., 500mg")
        form_layout.addRow("Dose:", self.input_dose)
        
        # Web Search Toggle
        self.web_search_toggle = QCheckBox("Enable Web Search (Include active web links)")
        self.web_search_toggle.setChecked(True)
        form_layout.addRow("Web Search:", self.web_search_toggle)
        
        self.layout.addLayout(form_layout)
        
        # Search Button
        self.btn_search = QPushButton("Look Up in Sources")
        self.btn_search.clicked.connect(self.perform_lookup)
        self.layout.addWidget(self.btn_search)
        
        # Results Display
        self.results_display = QTextBrowser()
        self.results_display.setPlaceholderText("Results will appear here based STRICTLY on your active sources...")
        self.layout.addWidget(self.results_display)

    def perform_lookup(self):
        name = self.input_name.text().strip()
        dose = self.input_dose.text().strip()
        
        if not name or not dose:
            self.results_display.setHtml("<p style='color:red;'>Please enter both Medication Name and Dose.</p>")
            return
            
        self.results_display.setHtml(f"<p>Searching active sources for <b>{name} {dose}</b>...</p>")
        
        # Initialize Engine 
        engine = LookupEngine()
        result = engine.search_medication(name, dose, allow_web=self.web_search_toggle.isChecked())
        
        # Format the result HTML
        html = f"""
        <h3>Lookup Results for: {result['medication']} {result['dose']}</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="background-color: #f0f0f0;" colspan="2"><b>Code Information</b></td>
            </tr>
            <tr>
                <td><b>ATC Code(s)</b></td>
                <td>{result.get('atc_codes', 'Not Found')}</td>
            </tr>
        """
        
        matches = result.get("matches", [])
        if not matches:
            html += """
            <tr>
                <td colspan="2"><i>No formulation matches found in active sources.</i></td>
            </tr>
            """
        else:
            for match in matches:
                bg_color = "#e0ffe0" if "bnf" in match["source"].lower() else "#e0f0ff"
                html += f"""
                <tr>
                    <td style="background-color: {bg_color};" colspan="2"><b>{match['source']}</b></td>
                </tr>
                <tr>
                    <td><b>Formulation</b></td>
                    <td>{match.get('formulation', 'Not Found')}</td>
                </tr>
                <tr>
                    <td><b>Active Ingredient</b></td>
                    <td>{match.get('active_ingredient', 'Not Found')}</td>
                </tr>
                <tr>
                    <td><b>Price</b></td>
                    <td>{match.get('price', 'Not Found')}</td>
                </tr>
                <tr>
                    <td><b>Packet Size</b></td>
                    <td>{match.get('packet_size', 'Not Found')}</td>
                </tr>
                """
                if match.get("category") and match["category"] != "Not Found":
                    html += f"""
                    <tr>
                        <td><b>Category</b></td>
                        <td>{match['category']}</td>
                    </tr>
                    """

        html += f"""
        </table>
        
        <br/>
        <b>Source Citation(s):</b>
        <p>{result.get('sources', 'No sources matched.')}</p>
        """
        
        self.results_display.setHtml(html)
