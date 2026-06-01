# Medication Lookup Application

A comprehensive tool designed for searching and processing medication data. The application offers both a desktop version and a web-based version for flexible usage.

## Features

- **Single Lookup**: Search for individual medications and their details.
- **Bulk Processing**: Upload Excel/CSV files to process multiple medications at once.
- **Source Library**: View and index underlying data sources (such as the NHS Drug Tariff List).
- **Dual Interface**: Includes both a robust desktop application and an accessible web version.

## Project Structure

- `app/` - The desktop application (built with PySide6/Qt). Contains core logic, database management, and the UI.
- `webapp/` - The web-based version (built with Streamlit) offering similar functionality directly in the browser.
- `storage/` - Directory designated for necessary Excel spreadsheets or data sources.
- `Packaging_Documentation.qmd` / `.html` - Documentation covering how the desktop application is compiled into a standalone installer.

## Getting Started

### Prerequisites

Ensure you have Python 3 installed. You can install all dependencies via `pip`.

```bash
pip install -r requirements.txt
```

### Running the Desktop App

Navigate to the `app/` directory and run the main script:

```bash
cd app
python main.py
```

### Running the Web App

Navigate to the `webapp/` directory and use Streamlit to run the web interface:

```bash
cd webapp
streamlit run app.py
```

## Packaging the App (Desktop)

The application can be packaged into a standalone Windows installer using PyInstaller and Inno Setup. Please refer to `Packaging_Documentation.html` or `Packaging_Documentation.qmd` for detailed instructions on the compilation and packaging pipeline.

## Author

Bea_EFD
