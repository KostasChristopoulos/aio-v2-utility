# AIO v2 - All-In-One CSV & Excel Utility

A Python-based utility tool for common CSV and Excel data processing tasks.

## 🚀 Downloads
**[Download AIO Tool v2.5 for macOS](https://github.com/KostasChristopoulos/aio-v2-utility/releases/latest/download/AIO_CSV_Tool_macOS.zip)**  
*(For Windows/Linux, run via Python instructions below)*

---

## Features
- **CSV Batch Splitter**: Splits large CSV files into smaller batches with built-in validation and duplicate detection.
- **CSV Column Dropper**: Removes specific columns from CSV files.
- **Array to String Converter**: Converts array-style text data into pipe-delimited strings.
- **CSV Concatenator**: Merges multiple CSV files from a folder with automatic column matching and empty column cleanup.
- **Excel to CSV**: Converts Excel workbooks or specific sheets into CSV files.
- **Date Harmonizer**: Automatically detects and converts diverse date formats into a unified target format (e.g., YYYY-MM-DD for DBs), with support for US/EU ambiguity resolution.
- **Activity Log**: Real-time logging with color-coded status, error/warning counters, and session export to .txt.

## Quality of Life
- **Drag & Drop**: Drop files or folders directly into the app.
- **Smart Naming**: Automatically suggests output filenames based on the input.
- **Finder Integration**: Option to open the results folder directly after processing.
- **Copy logs**: Double-click any log line to copy it to your clipboard.

## 🛠️ Installation & Usage

1. **Prerequisites**: [Python 3.10+](https://www.python.org/downloads/)
2. **Install Dependencies**:
   ```bash
   pip install customtkinter pandas Pillow tkinterdnd2 openpyxl
   ```
3. **Run**:
   ```bash
   python main.py
   ```

---
See [CHANGELOG.md](CHANGELOG.md) for version history.
