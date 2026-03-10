# AIO v2 - All-In-One CSV & Excel Power Tool

A professional-grade Python utility for ultra-fast data processing. Designed for scalability and ease of use.

## 🚀 Downloads
**[Download AIO Tool v2.5 for macOS](https://github.com/KostasChristopoulos/aio-v2-utility/releases/latest/download/AIO_CSV_Tool_macOS.zip)**  
*(For Windows/Linux, please run via Python instructions below)*

---

## 🔥 Features
- **📊 CSV Batch Splitter**: Ultra-fast splitting with built-in ASSET_ID duplicate detection.
- **✂️ CSV Column Dropper**: Instantly remove specific columns with dynamic header detection.
- **🔄 Array to String Converter**: Cleans array-style data into clean, pipe-delimited strings.
- **🔗 Smart CSV Concatenator**: 
    - Auto-detects common columns.
    - Flags "Disconnected Files" with mismatched headers.
    - **Unique NULL Dropper**: Automatically purges empty columns during join.
- **📗 Excel to CSV**: Batch convert Excel workbooks or specific sheets in seconds.
- **🖥️ Pro Activity Log**:
    - Color-coded events (Success, Warning, Error, Alert).
    - **Live Counters**: Track process health at a glance.
    - **Exportable**: Save session logs to `.txt`.
    - **Snippet Snapping**: Double-click any line to copy to clipboard.
- **🎯 QoL Extras**: 
    - Smart output naming.
    - Reveal in Finder shortcuts.
    - Full Drag & Drop integration.

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

## 📜 Version History
See [CHANGELOG.md](CHANGELOG.md) for full milestone details.
