import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import json
from datetime import datetime
from PIL import Image, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES
import pandas as pd
import subprocess
import platform
import urllib.request
from tkinter import Menu

from tools.csv_splitter import process_split
from tools.csv_dropper import process_drop
from tools.csv_array_converter import process_convert
from tools.csv_concat import process_concat, get_common_columns
from tools.xlsx_to_csv import process_xlsx_convert, get_sheet_names
from tools.date_harmonizer import process_date_harmonization

# ==========================================
# TOOLTIP SYSTEM
# ==========================================
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

    def show_tip(self):
        if self.tip_window or not self.text: return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        if platform.system() == "Darwin":
            tw.attributes("-alpha", 0.95)
        
        # Use a Frame for the background and border
        frame = ctk.CTkFrame(tw, corner_radius=6, 
                             fg_color=("#E0E0E0", "#333333"), 
                             border_width=1, border_color="gray40")
        frame.pack()

        label = ctk.CTkLabel(frame, text=self.text, justify="left",
                             text_color=("#202020", "#EEEEEE"),
                             font=("Inter", 11))
        label.pack(padx=10, pady=5)

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def add_info_icon(parent, text):
    lbl = ctk.CTkLabel(parent, text="ⓘ", font=("Inter", 15), text_color="gray50", cursor="hand2")
    tip = Tooltip(lbl, text)
    lbl.bind("<Enter>", lambda e: tip.show_tip())
    lbl.bind("<Leave>", lambda e: tip.hide_tip())
    return lbl

# ==========================================
# 1. CORE APP SETUP & NAVIGATION
# ==========================================
VERSION = "v2.8.0"
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
ENABLE_ACTIVITY_LOG = True 

# Global Log State
log_counts = {"warning": 0, "error": 0, "alert": 0}
log_minimized = False

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f)
    except Exception as e:
        print(f"Error saving config: {e}")

class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = Tk()

def check_for_updates():
    try:
        url = "https://api.github.com/repos/KostasChristopoulos/aio-v2-utility/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "")
            if latest_version and latest_version != VERSION:
                def prompt_update():
                    dialog = ctk.CTkToplevel(root)
                    dialog.title("Update Available")
                    dialog.geometry("350x180")
                    dialog.attributes("-topmost", True)
                    
                    if platform.system() == "Darwin":
                        dialog.attributes("-alpha", 0.95)
                    
                    ctk.CTkLabel(dialog, text=f"A new version ({latest_version}) is available!\n\nYou are currently using {VERSION}.\nWould you like to download it?", font=("Inter", 12)).pack(pady=(20, 15))
                    
                    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
                    btn_frame.pack(pady=10)
                    
                    def download_update():
                        dialog.destroy()
                        asset_url = None
                        for asset in data.get("assets", []):
                            if "AIO_CSV_Tool" in asset.get("name", "") and asset.get("name", "").endswith(".zip"):
                                asset_url = asset.get("browser_download_url")
                                break
                        
                        if not asset_url:
                            import webbrowser
                            webbrowser.open(data.get("html_url"))
                            return
                            
                        download_dialog = ctk.CTkToplevel(root)
                        download_dialog.title("Downloading Update")
                        download_dialog.geometry("300x120")
                        download_dialog.attributes("-topmost", True)
                        ctk.CTkLabel(download_dialog, text="Downloading to Downloads folder...").pack(pady=20)
                        progress = ctk.CTkProgressBar(download_dialog)
                        progress.pack(pady=10, padx=20)
                        progress.start()
                        
                        def download_thread():
                            if not asset_url:
                                def fail():
                                    progress.stop()
                                    download_dialog.destroy()
                                    messagebox.showerror("Error", "No download URL found.")
                                root.after(0, fail)
                                return
                            try:
                                downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', f"AIO_CSV_Tool_{latest_version}.zip")
                                opener = urllib.request.build_opener()
                                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                                urllib.request.install_opener(opener)
                                urllib.request.urlretrieve(asset_url, downloads_path)
                                def finish():
                                    progress.stop()
                                    download_dialog.destroy()
                                    messagebox.showinfo("Update Downloaded", f"Update downloaded to:\n{downloads_path}\n\nPlease extract and use the new version.")
                                root.after(0, finish)
                            except Exception as e:
                                def fail():
                                    progress.stop()
                                    download_dialog.destroy()
                                    messagebox.showerror("Error", f"Failed to download update:\n{e}")
                                root.after(0, fail)
                                
                        threading.Thread(target=download_thread, daemon=True).start()
                    
                    ctk.CTkButton(btn_frame, text="Yes, Download", command=download_update, width=120, font=("Inter", 12, "bold")).pack(side="left", padx=5)
                    ctk.CTkButton(btn_frame, text="Skip", command=dialog.destroy, width=80, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="left", padx=5)
                    
                root.after(3000, prompt_update)  # Prompt 3s after UI loads
    except Exception as e:
        print(f"Update check failed: {e}")

threading.Thread(target=check_for_updates, daemon=True).start()
root.title("AIO v2")
root.geometry("750x550")

# Add Icon
icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
if os.path.exists(icon_path):
    icon_image = ImageTk.PhotoImage(Image.open(icon_path))
    root.iconphoto(True, icon_image)


# --- Log Management Functions ---
def log_message(msg, level="info"):
    print(f"[{level.upper()}] {msg}")
    if ENABLE_ACTIVITY_LOG and 'textbox_log' in globals():
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level in log_counts:
            log_counts[level] += 1
            update_log_header_stats()
        def _insert():
            textbox_log.configure(state="normal")
            textbox_log.insert("end", f"[{timestamp}] ", "timestamp")
            textbox_log.insert("end", f"{msg}\n", level.lower())
            textbox_log.see("end")
            textbox_log.configure(state="disabled")
        root.after(0, _insert)

def update_log_header_stats():
    if 'lbl_log_stats' in globals():
        stats_text = f"Warnings: {log_counts['warning']} | Errors: {log_counts['error'] + log_counts['alert']}"
        lbl_log_stats.configure(text=stats_text)

def clear_log():
    if 'textbox_log' in globals():
        textbox_log.configure(state="normal")
        textbox_log.delete("1.0", "end")
        textbox_log.configure(state="disabled")
        for k in log_counts: log_counts[k] = 0
        update_log_header_stats()
        log_message("Log cleared.", "info")

def save_log():
    if 'textbox_log' in globals():
        content = textbox_log.get("1.0", "end-1c")
        if not content.strip(): return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"aio_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if file_path:
            with open(file_path, "w") as f:
                f.write(content)
            log_message(f"Log exported to: {os.path.basename(file_path)}", "success")

def copy_log_to_clipboard(event=None):
    if 'textbox_log' in globals():
        # Get the line index where the user clicked
        try:
            # We get the index from the click coordinates or current insertion point
            line_idx = textbox_log.index(f"@{event.x},{event.y}")
            line_start = f"{line_idx.split('.')[0]}.0"
            line_end = f"{line_idx.split('.')[0]}.end"
            
            line_content = textbox_log.get(line_start, line_end).strip()
            
            if line_content:
                root.clipboard_clear()
                root.clipboard_append(line_content)
        except Exception:
            pass

def toggle_log():
    global log_minimized
    if log_minimized:
        log_frame.configure(height=130)
        btn_toggle_log.configure(text="▼")
        log_minimized = False
    else:
        log_frame.configure(height=35)
        btn_toggle_log.configure(text="▲")
        log_minimized = True

# --- QoL Global Helpers ---
def get_file_stats(filepath):
    try:
        if filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath, nrows=0)
            cols = len(df.columns)
            row_count = sum(1 for _ in open(filepath)) - 1
            return f"{row_count:,} rows, {cols:,} columns"
        elif filepath.lower().endswith(('.xlsx', '.xls')):
            xl = pd.ExcelFile(filepath)
            df = xl.parse(xl.sheet_names[0], nrows=0)
            return f"Excel: {len(xl.sheet_names)} sheets, {len(df.columns)} columns"
    except Exception:
        return ""
    return ""

def update_stats_label(filepath, label_widget):
    stats = get_file_stats(filepath)
    label_widget.configure(text=stats if stats else "")

def suggest_output_name(input_path, entry_widget):
    base = os.path.basename(input_path).rsplit('.', 1)[0]
    entry_widget.delete(0, "end")
    entry_widget.insert(0, base)

def open_folder(path):
    if os.path.isdir(path):
        subprocess.run(['open', path])
    else:
        subprocess.run(['open', os.path.dirname(path)])

def show_open_folder_btn(folder_path, page):
    if hasattr(page, 'btn_open_folder'):
        page.btn_open_folder.destroy()
    page.btn_open_folder = ctk.CTkButton(page, text="📁 Reveal results in Finder", 
                                       command=lambda: open_folder(folder_path),
                                       fg_color="transparent", border_width=1,
                                       text_color=("gray10", "gray90"))
    page.btn_open_folder.pack(pady=5)

def add_standard_shortcuts(root):
    """Adds standard Mac Command-key shortcuts (Paste, Copy, etc.) globally."""
    if platform.system() == "Darwin":
        root.bind_all("<Command-v>", lambda e: e.widget.event_generate("<<Paste>>"))
        root.bind_all("<Command-c>", lambda e: e.widget.event_generate("<<Copy>>"))
        root.bind_all("<Command-x>", lambda e: e.widget.event_generate("<<Cut>>"))
        root.bind_all("<Command-a>", lambda e: e.widget.event_generate("<<SelectAll>>"))

def show_context_menu(event):
    """Universal right-click menu for Entry and Text widgets."""
    try:
        w = event.widget
        m = Menu(None, tearoff=0)
        m.add_command(label="Cut", command=lambda: w.event_generate("<<Cut>>"))
        m.add_command(label="Copy", command=lambda: w.event_generate("<<Copy>>"))
        m.add_command(label="Paste", command=lambda: w.event_generate("<<Paste>>"))
        m.add_separator()
        m.add_command(label="Select All", command=lambda: w.event_generate("<<SelectAll>>"))
        m.tk_popup(event.x_root, event.y_root)
    except Exception:
        pass

# ==========================================
# 2. LOGIC: CSV SPLITTER
# ==========================================
def browse_file_split():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        entry_filepath_split.delete(0, "end")
        entry_filepath_split.insert(0, filename)
        suggest_output_name(filename, entry_output_name)
        update_stats_label(filename, lbl_stats_split)
        load_splitter_columns(filename)

def load_splitter_columns(filepath):
    try:
        df_head = pd.read_csv(filepath, nrows=0)
        cols = df_head.columns.tolist()
        combo_unique_id.configure(values=["(None)"] + cols)
        if "ASSET_ID" in cols: combo_unique_id.set("ASSET_ID")
        elif "CUSTOM_ID" in cols: combo_unique_id.set("CUSTOM_ID")
        else: combo_unique_id.set("(None)")
    except Exception:
        pass

def run_splitter():
    input_file = entry_filepath_split.get()
    output_name = entry_output_name.get()
    create_test = check_test_split.get()
    drop_dups = check_drop_dups.get()
    unique_col = combo_unique_id.get()
    if unique_col == "(None)": unique_col = None
    try:
        rows_per_batch = int(entry_rows.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for rows per batch.")
        return
    if not input_file or not output_name:
        messagebox.showerror("Error", "Please make sure all fields are filled out.")
        return
    btn_run_split.configure(state="disabled", text="Processing...")
    progress_split.set(0); progress_split.pack(pady=10)
    def on_progress(current, total):
        pct = current / total if total > 0 else 0
        root.after(0, lambda: progress_split.set(pct))
    def on_complete(success, message):
        def ui_update():
            btn_run_split.configure(state="normal", text="Run Splitter"); progress_split.pack_forget()
            if success: log_message(message, "success")
            else: log_message(f"Validation Failed: {message}", "warning")
            messagebox.showinfo("Status", message)
        root.after(0, ui_update)
    def on_error(error_msg):
        def ui_error():
            btn_run_split.configure(state="normal", text="Run Splitter"); progress_split.pack_forget()
            log_message(f"Error: {error_msg}", "error")
            messagebox.showerror("Error", error_msg)
        root.after(0, ui_error)
    log_message(f"Started splitting {os.path.basename(input_file)}...", "info")
    thread = threading.Thread(target=process_split, args=(input_file, output_name, rows_per_batch, unique_col, create_test, on_progress, on_complete, on_error, drop_dups))
    thread.daemon = True; thread.start()
    show_open_folder_btn(os.path.dirname(input_file), page_splitter)

# ==========================================
# 3. LOGIC: COLUMN DROPPER
# ==========================================
def browse_file_drop():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        entry_filepath_drop.delete(0, "end"); entry_filepath_drop.insert(0, filename)
        load_detected_columns(filename)
        update_stats_label(filename, lbl_stats_drop)

def load_detected_columns(filepath):
    try:
        df_head = pd.read_csv(filepath, nrows=0)
        cols = df_head.columns.tolist()
        combo_cols.configure(values=cols); combo_cols.set("Pick a column to add...")
        log_message(f"Detected {len(cols)} columns in {os.path.basename(filepath)}", "info")
    except Exception as e:
        log_message(f"Could not read headers: {e}", "error")

def add_column_to_entry(col_name):
    if col_name == "Pick a column to add...": return
    current = entry_columns.get().strip()
    if current:
        if col_name not in current.split(';'):
            entry_columns.delete(0, "end")
            entry_columns.insert(0, f"{current};{col_name}")
    else: entry_columns.insert(0, col_name)

def run_dropper():
    input_file = entry_filepath_drop.get(); columns_raw = entry_columns.get()
    if not input_file or not columns_raw:
        messagebox.showerror("Error", "Please provide a file path and at least one column name."); return
    btn_run_drop.configure(state="disabled", text="Processing...")
    progress_drop.pack(pady=10); progress_drop.start()
    def on_complete(num_dropped, warning_msg):
        def ui_update():
            progress_drop.stop(); progress_drop.pack_forget()
            btn_run_drop.configure(state="normal", text="Drop & Save")
            if warning_msg: log_message(f"Warning: {warning_msg}", "warning")
            log_message(f"Successfully targeted {num_dropped} column(s) and updated the file.", "success")
            messagebox.showinfo("Success!", "File updated.")
        root.after(0, ui_update)
    def on_error(error_msg):
        def ui_error():
            progress_drop.stop(); progress_drop.pack_forget()
            btn_run_drop.configure(state="normal", text="Drop & Save")
            log_message(f"Error: {error_msg}", "error"); messagebox.showerror("Error", error_msg)
        root.after(0, ui_error)
    log_message(f"Started column drop on {os.path.basename(input_file)}...", "info")
    thread = threading.Thread(target=process_drop, args=(input_file, columns_raw, on_complete, on_error))
    thread.daemon = True; thread.start()

# ==========================================
# 4. LOGIC: ARRAY CONVERTER
# ==========================================
def browse_file_convert():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        entry_filepath_convert.delete(0, "end"); entry_filepath_convert.insert(0, filename)
        update_stats_label(filename, lbl_stats_convert)

def run_converter():
    input_file = entry_filepath_convert.get()
    if not input_file: messagebox.showerror("Error", "Please provide a file path."); return
    btn_run_convert.configure(state="disabled", text="Processing...")
    progress_convert.pack(pady=10); progress_convert.start()
    def on_complete(output_file):
        def ui_update():
            progress_convert.stop(); progress_convert.pack_forget()
            btn_run_convert.configure(state="normal", text="Convert Arrays to Strings")
            log_message(f"Success: {os.path.basename(output_file)}", "success")
            show_open_folder_btn(os.path.dirname(output_file), page_converter)
            messagebox.showinfo("Success!", "Conversion complete.")
        root.after(0, ui_update)
    def on_error(error_msg):
        def ui_error():
            progress_convert.stop(); progress_convert.pack_forget()
            btn_run_convert.configure(state="normal", text="Convert Arrays to Strings")
            log_message(f"Error: {error_msg}", "error"); messagebox.showerror("Error", error_msg)
        root.after(0, ui_error)
    log_message(f"Converting arrays in {os.path.basename(input_file)}...", "info")
    thread = threading.Thread(target=process_convert, args=(input_file, on_complete, on_error))
    thread.daemon = True; thread.start()

# ==========================================
# 5. LOGIC: CSV CONCAT
# ==========================================
def browse_folder_concat():
    foldername = filedialog.askdirectory()
    if foldername:
        entry_folderpath_concat.delete(0, "end"); entry_folderpath_concat.insert(0, foldername)
        suggest_output_name(foldername, entry_concat_output)
        load_folder_columns(foldername)

def load_folder_columns(folder_path):
    log_message(f"Scanning folder for common columns...", "info")
    common_cols, disconnected = get_common_columns(folder_path)
    if disconnected:
        # Cast to list[str] to satisfy strict IDE type checking
        disc_list = [str(f) for f in disconnected]
        log_message(f"🚨 ALERT: {len(disc_list)} file(s) disconnected: {', '.join(disc_list)}", "alert")
    else: log_message("Folder scan complete. No disconnected files found.", "success")
    
    # Ensure common_cols is treated as a list of strings
    safe_cols = [str(c) for c in common_cols]
    options = ["All Columns (Suggest if headers match)"] + safe_cols
    combo_concat_cols.configure(values=options)
    combo_concat_cols.set("All Columns (Suggest if headers match)")
    log_message(f"Found {len(common_cols)} columns present in ALL files.", "info")

def run_concat_logic():
    folder_path = entry_folderpath_concat.get(); output_name = entry_concat_output.get()
    sel_col = combo_concat_cols.get()
    target_col = None if sel_col == "All Columns (Suggest if headers match)" else sel_col
    if not folder_path or not output_name:
        messagebox.showerror("Error", "Please provide folder path and output name."); return
    btn_run_concat.configure(state="disabled", text="Processing...")
    progress_concat.set(0); progress_concat.pack(pady=10)
    def on_progress(current, total):
        pct = current / total if total > 0 else 0
        root.after(0, lambda: progress_concat.set(pct))
    def on_complete(success, message):
        def ui_update():
            if not success and message.startswith("LOG:"):
                log_message(message[4:].strip(), "warning"); return
            btn_run_concat.configure(state="normal", text="Concatenate"); progress_concat.pack_forget()
            log_message(message, "success" if success else "warning"); messagebox.showinfo("Status", message)
            if success: show_open_folder_btn(folder_path, page_concat)
        root.after(0, ui_update)
    def on_error(error_msg):
        def ui_error():
            btn_run_concat.configure(state="normal", text="Concatenate"); progress_concat.pack_forget()
            log_message(f"Error: {error_msg}", "error"); messagebox.showerror("Error", error_msg)
        root.after(0, ui_error)
    log_message(f"Concatenating {os.path.basename(folder_path)}...", "info")
    thread = threading.Thread(target=process_concat, args=(folder_path, output_name, target_col, on_progress, on_complete, on_error))
    thread.daemon = True; thread.start()

# ==========================================
# 6. LOGIC: XLSX TO CSV
# ==========================================
def browse_file_xlsx():
    filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if filename:
        entry_filepath_xlsx.delete(0, "end"); entry_filepath_xlsx.insert(0, filename)
        suggest_output_name(filename, entry_output_xlsx)
        update_stats_label(filename, lbl_stats_xlsx)
        load_excel_sheets(filename)

def load_excel_sheets(filepath):
    sheets = get_sheet_names(filepath)
    if sheets:
        sheet_options = ["All"] + sheets
        combo_xlsx_sheets.configure(values=sheet_options); combo_xlsx_sheets.set("All")
        log_message(f"Excel detected: {len(sheets)} sheets.", "info")

def run_xlsx_converter_logic():
    input_file = entry_filepath_xlsx.get(); sheet = combo_xlsx_sheets.get()
    if not input_file: messagebox.showerror("Error", "Please provide a file."); return
    btn_run_xlsx.configure(state="disabled", text="Processing...")
    progress_xlsx.pack(pady=10); progress_xlsx.start()
    def on_complete(msg):
        def ui_update():
            progress_xlsx.stop(); progress_xlsx.pack_forget()
            btn_run_xlsx.configure(state="normal", text="Convert Excel to CSV")
            log_message(msg, "success"); show_open_folder_btn(os.path.dirname(input_file), page_xlsx)
            messagebox.showinfo("Success!", msg)
        root.after(0, ui_update)
    def on_error(error_msg):
        def ui_error():
            progress_xlsx.stop(); progress_xlsx.pack_forget()
            btn_run_xlsx.configure(state="normal", text="Convert Excel to CSV")
            log_message(f"Error: {error_msg}", "error"); messagebox.showerror("Error", error_msg)
        root.after(0, ui_error)
    log_message(f"Converting Excel file {os.path.basename(input_file)}...", "info")
    thread = threading.Thread(target=process_xlsx_convert, args=(input_file, sheet, on_complete, on_error))
    thread.daemon = True; thread.start()

# ==========================================
# 7. LOGIC: DATE HARMONIZER
# ==========================================
def browse_file_dates():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        entry_filepath_dates.delete(0, "end"); entry_filepath_dates.insert(0, filename)
        update_stats_label(filename, lbl_stats_dates)
        load_date_columns(filename)

def load_date_columns(filepath):
    try:
        # Scan first 50 rows to find likely date columns
        df = pd.read_csv(filepath, nrows=50)
        date_cols = []
        for col in df.columns:
            # Simple heuristic: look for numbers, separators, or common date keywords
            sample = df[col].dropna().astype(str).tolist()
            if any(any(char in s for char in '/-') and any(char.isdigit() for char in s) for s in sample):
                date_cols.append(col)
        
        if date_cols:
            log_message(f"Detected {len(date_cols)} potential date columns.", "info")
            combo_date_cols.configure(values=date_cols)
            combo_date_cols.set(date_cols[0])
        else:
            log_message("No obvious date columns detected, showing all columns.", "warning")
            combo_date_cols.configure(values=df.columns.tolist())
            combo_date_cols.set(df.columns[0])
    except Exception as e:
        log_message(f"Date scan failed: {e}", "error")

def add_date_col_to_list(col_name):
    current = entry_target_date_cols.get().strip()
    if current:
        if col_name not in current.split(';'):
            entry_target_date_cols.insert("end", f";{col_name}")
    else:
        entry_target_date_cols.insert(0, col_name)

def run_date_harmonizer():
    input_file = entry_filepath_dates.get()
    cols_raw = entry_target_date_cols.get()
    pref = combo_date_pref.get() # 'US (MM/DD)' or 'EU (DD/MM)'
    target_fmt = combo_date_format.get()
    
    # Map friendly names to strftime
    fmt_map = {
        "YYYY-MM-DD (Snowflake)": "%Y-%m-%d",
        "DD-MM-YYYY": "%d-%m-%Y",
        "MM-DD-YYYY": "%m-%d-%Y",
        "DD/MM/YYYY": "%d/%m/%Y",
        "MM/DD/YYYY": "%m/%d/%Y",
        "DD-MMM-YYYY (e.g. 15-Mar-2024)": "%d-%b-%Y"
    }
    fmt = fmt_map.get(target_fmt, "%Y-%m-%d")
    pref_clean = 'EU' if 'EU' in pref else 'US'
    
    if not input_file or not cols_raw:
        messagebox.showerror("Error", "Please provide a file and target columns."); return
    
    target_cols = [c.strip() for c in cols_raw.split(';') if c.strip()]
    btn_run_dates.configure(state="disabled", text="Processing...")
    progress_dates.pack(pady=10); progress_dates.set(0)
    
    def on_progress(curr, total):
        pct = curr / total if total > 0 else 0
        root.after(0, lambda: progress_dates.set(pct))
        
    def on_complete(success, msg, out_file):
        def ui_update():
            progress_dates.pack_forget()
            btn_run_dates.configure(state="normal", text="Harmonize Dates")
            log_message(msg, "success" if success else "warning")
            if success: show_open_folder_btn(os.path.dirname(input_file), page_dates)
            messagebox.showinfo("Status", msg)
        root.after(0, ui_update)
        
    def on_error(err):
        def ui_error():
            progress_dates.pack_forget()
            btn_run_dates.configure(state="normal", text="Harmonize Dates")
            log_message(f"Error: {err}", "error"); messagebox.showerror("Error", err)
        root.after(0, ui_error)
        
    log_message(f"Harmonizing dates in {os.path.basename(input_file)}...", "info")
    thread = threading.Thread(target=process_date_harmonization, args=(input_file, target_cols, pref_clean, fmt, on_progress, on_complete, on_error))
    thread.daemon = True; thread.start()

# ==========================================
# 8. LAYOUT & PAGES
# ==========================================
root.grid_rowconfigure(0, weight=1); root.grid_columnconfigure(1, weight=1)
sidebar = ctk.CTkFrame(root, width=170, corner_radius=0); sidebar.grid(row=0, column=0, sticky="nsew")
content = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent"); content.grid(row=0, column=1, sticky="nsew")
content.grid_rowconfigure(0, weight=1); content.grid_columnconfigure(0, weight=1)

if ENABLE_ACTIVITY_LOG:
    content.grid_rowconfigure(1, weight=0)
    log_frame = ctk.CTkFrame(content, height=130, corner_radius=0); log_frame.grid(row=1, column=0, sticky="ew")
    log_frame.pack_propagate(False)
    log_header = ctk.CTkFrame(log_frame, fg_color="transparent", height=30); log_header.pack(fill="x", padx=10, pady=(2, 0))
    btn_toggle_log = ctk.CTkButton(log_header, text="▼", width=25, height=20, command=toggle_log, fg_color="transparent"); btn_toggle_log.pack(side="left", padx=(0, 5))
    ctk.CTkLabel(log_header, text="Activity Log", font=("Inter", 12, "bold")).pack(side="left")
    lbl_log_stats = ctk.CTkLabel(log_header, text="Warnings: 0 | Errors: 0", font=("Inter", 11), text_color="gray50"); lbl_log_stats.pack(side="left", padx=20)
    ctk.CTkButton(log_header, text="Clear", width=50, height=20, font=("Inter", 10), command=clear_log, fg_color="transparent", border_width=1).pack(side="right", padx=2)
    ctk.CTkButton(log_header, text="Save", width=50, height=20, font=("Inter", 10), command=save_log, fg_color="transparent", border_width=1).pack(side="right", padx=2)
    textbox_log = ctk.CTkTextbox(log_frame, font=("Courier", 11)); textbox_log.pack(fill="both", expand=True, padx=10, pady=(0, 5))
    textbox_log.bind("<Double-Button-1>", copy_log_to_clipboard)
    textbox_log.tag_config("timestamp", foreground="#888888")
    textbox_log.tag_config("info", foreground="#AAB0B8")
    textbox_log.tag_config("success", foreground="#2ECC71")
    textbox_log.tag_config("warning", foreground="#F1C40F")
    textbox_log.tag_config("error", foreground="#E74C3C")
    textbox_log.tag_config("alert", foreground="#E91E63")
    textbox_log.configure(state="disabled")
    log_message("Application initialized.", "info")

page_splitter = ctk.CTkFrame(content, fg_color="transparent"); page_splitter.grid(row=0, column=0, sticky="nsew")
page_dropper = ctk.CTkFrame(content, fg_color="transparent"); page_dropper.grid(row=0, column=0, sticky="nsew")
page_converter = ctk.CTkFrame(content, fg_color="transparent"); page_converter.grid(row=0, column=0, sticky="nsew")
page_concat = ctk.CTkFrame(content, fg_color="transparent"); page_concat.grid(row=0, column=0, sticky="nsew")
page_xlsx = ctk.CTkFrame(content, fg_color="transparent"); page_xlsx.grid(row=0, column=0, sticky="nsew")

# --- UI: Splitter ---
ctk.CTkLabel(page_splitter, text="CSV Batch Splitter", font=("Inter", 24, "bold")).pack(pady=20)
f1 = ctk.CTkFrame(page_splitter, fg_color="transparent"); f1.pack(fill="x", padx=40)
entry_filepath_split = ctk.CTkEntry(f1); entry_filepath_split.pack(side="left", expand=True, fill="x", padx=5)
ctk.CTkButton(f1, text="Browse", command=browse_file_split, width=80).pack(side="left")
lbl_stats_split = ctk.CTkLabel(page_splitter, text="", font=("Inter", 11), text_color="gray50"); lbl_stats_split.pack()
f_rows = ctk.CTkFrame(page_splitter, fg_color="transparent"); f_rows.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f_rows, text="Rows per batch:", width=120).pack(side="left")
entry_rows = ctk.CTkEntry(f_rows); entry_rows.insert(0, "5000"); entry_rows.pack(side="left", expand=True, fill="x")
add_info_icon(f_rows, "Number of rows per split file.").pack(side="left", padx=5)

f_out = ctk.CTkFrame(page_splitter, fg_color="transparent"); f_out.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f_out, text="Output Name:", width=120).pack(side="left")
entry_output_name = ctk.CTkEntry(f_out); entry_output_name.pack(side="left", expand=True, fill="x")
add_info_icon(f_out, "The filename prefix for all generated batches.\nExample: 'MyReport' becomes 'MyReport_Batch1.csv'").pack(side="left", padx=5)

f_uid = ctk.CTkFrame(page_splitter, fg_color="transparent"); f_uid.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f_uid, text="Unique ID Column:", width=120).pack(side="left")
combo_unique_id = ctk.CTkOptionMenu(f_uid, values=["(None)"]); combo_unique_id.pack(side="left", expand=True, fill="x")
add_info_icon(f_uid, "Select a column containing unique identifiers (e.g., ASSET_ID).\nThe tool will check for duplicates within this column\nand report them back in window").pack(side="left", padx=5)

check_test_split = ctk.BooleanVar(value=True)
check_drop_dups = ctk.BooleanVar(value=True)

f_opts = ctk.CTkFrame(page_splitter, fg_color="transparent"); f_opts.pack(pady=5)
chk_test = ctk.CTkCheckBox(f_opts, text="Create Test File (First 10 rows)?", variable=check_test_split, font=("Inter", 12))
chk_test.pack(side="left", padx=2)
add_info_icon(f_opts, "Creates a small 10-row file titled '_Test.csv' to verify your delivery template.").pack(side="left", padx=(0, 15))

chk_drop = ctk.CTkCheckBox(f_opts, text="Drop True Duplicates?", variable=check_drop_dups, font=("Inter", 12))
chk_drop.pack(side="left", padx=2)
add_info_icon(f_opts, "True Duplicate: A row that is 100% identical to another across ALL columns.\nIf this is ON these rows will be dropped automatically").pack(side="left", padx=5)

btn_run_split = ctk.CTkButton(page_splitter, text="Run Splitter", command=run_splitter, font=("Inter", 14, "bold"), height=40); btn_run_split.pack(pady=10)
progress_split = ctk.CTkProgressBar(page_splitter, width=300); progress_split.set(0)

# --- UI: Dropper ---
ctk.CTkLabel(page_dropper, text="CSV Column Dropper", font=("Inter", 24, "bold")).pack(pady=20)
f2 = ctk.CTkFrame(page_dropper, fg_color="transparent"); f2.pack(fill="x", padx=40)
entry_filepath_drop = ctk.CTkEntry(f2); entry_filepath_drop.pack(side="left", expand=True, fill="x", padx=5)
ctk.CTkButton(f2, text="Browse", command=browse_file_drop, width=80).pack(side="left")
lbl_stats_drop = ctk.CTkLabel(page_dropper, text="", font=("Inter", 11), text_color="gray50"); lbl_stats_drop.pack()
f_cols = ctk.CTkFrame(page_dropper, fg_color="transparent"); f_cols.pack(fill="x", padx=40, pady=5)
entry_columns = ctk.CTkEntry(f_cols, placeholder_text="Columns to drop (split by ;)"); entry_columns.pack(side="left", expand=True, fill="x")
add_info_icon(f_cols, "List the exact column names to remove, separated by semicolons (;).\nExample: 'Internal_ID;Temp_Field'").pack(side="left", padx=5)

f_combo_drop = ctk.CTkFrame(page_dropper, fg_color="transparent"); f_combo_drop.pack(pady=5)
combo_cols = ctk.CTkOptionMenu(f_combo_drop, values=["Pick a column..."], command=add_column_to_entry, width=250); combo_cols.pack(side="left")
add_info_icon(f_combo_drop, "Quickly add a column to the list by picking it from this menu after browsing a file.").pack(side="left", padx=5)
btn_run_drop = ctk.CTkButton(page_dropper, text="Drop & Save", command=run_dropper, fg_color="#28a745", font=("Inter", 14, "bold"), height=40); btn_run_drop.pack(pady=10)
progress_drop = ctk.CTkProgressBar(page_dropper, width=300, mode="indeterminate")

# --- UI: Concat ---
ctk.CTkLabel(page_concat, text="CSV Concatenator", font=("Inter", 24, "bold")).pack(pady=20)
f3 = ctk.CTkFrame(page_concat, fg_color="transparent"); f3.pack(fill="x", padx=40)
entry_folderpath_concat = ctk.CTkEntry(f3, placeholder_text="Select Folder with CSVs"); entry_folderpath_concat.pack(side="left", expand=True, fill="x", padx=5)
ctk.CTkButton(f3, text="Browse", command=browse_folder_concat, width=80).pack(side="left")
f_concat_filter = ctk.CTkFrame(page_concat, fg_color="transparent"); f_concat_filter.pack(pady=5)
ctk.CTkLabel(f_concat_filter, text="Filter by Column (Join only these):", font=("Inter", 12, "italic")).pack(side="left")
combo_concat_cols = ctk.CTkOptionMenu(f_concat_filter, values=["All Columns (Suggest if headers match)"], width=300); combo_concat_cols.pack(side="left", padx=5)
add_info_icon(f_concat_filter, "Choose a specific column to keep during the join, or merge everything if headers match.").pack(side="left")
f4 = ctk.CTkFrame(page_concat, fg_color="transparent"); f4.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f4, text="Output Name:", width=120).pack(side="left")
entry_concat_output = ctk.CTkEntry(f4); entry_concat_output.insert(0, "combined"); entry_concat_output.pack(side="left", expand=True, fill="x")
add_info_icon(f4, "The name for your new merged CSV file.").pack(side="left", padx=5)
btn_run_concat = ctk.CTkButton(page_concat, text="Concatenate", command=run_concat_logic, font=("Inter", 14, "bold"), height=40); btn_run_concat.pack(pady=10)
progress_concat = ctk.CTkProgressBar(page_concat, width=300); progress_concat.set(0)

# --- UI: Excel ---
ctk.CTkLabel(page_xlsx, text="Excel to CSV Converter", font=("Inter", 24, "bold")).pack(pady=20)
f5 = ctk.CTkFrame(page_xlsx, fg_color="transparent"); f5.pack(fill="x", padx=40)
entry_filepath_xlsx = ctk.CTkEntry(f5); entry_filepath_xlsx.pack(side="left", expand=True, fill="x", padx=5)
ctk.CTkButton(f5, text="Browse", command=browse_file_xlsx, width=80).pack(side="left")
lbl_stats_xlsx = ctk.CTkLabel(page_xlsx, text="", font=("Inter", 11), text_color="gray50"); lbl_stats_xlsx.pack()
f6 = ctk.CTkFrame(page_xlsx, fg_color="transparent"); f6.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f6, text="Sheet:", width=120).pack(side="left")
combo_xlsx_sheets = ctk.CTkOptionMenu(f6, values=["All"]); combo_xlsx_sheets.pack(side="left", expand=True, fill="x")
add_info_icon(f6, "Convert a specific sheet, or 'All' to create a CSV for every sheet in the workbook.").pack(side="left", padx=5)
f_xl_out = ctk.CTkFrame(page_xlsx, fg_color="transparent"); f_xl_out.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f_xl_out, text="Output Name:", width=120).pack(side="left")
entry_output_xlsx = ctk.CTkEntry(f_xl_out); entry_output_xlsx.pack(side="left", expand=True, fill="x")
add_info_icon(f_xl_out, "Base name for the output file(s).").pack(side="left", padx=5)
btn_run_xlsx = ctk.CTkButton(page_xlsx, text="Convert Excel to CSV", command=run_xlsx_converter_logic, font=("Inter", 14, "bold"), height=40); btn_run_xlsx.pack(pady=10)
progress_xlsx = ctk.CTkProgressBar(page_xlsx, width=300, mode="indeterminate")

# --- UI: Array Conv ---
ctk.CTkLabel(page_converter, text="Array Converter", font=("Inter", 24, "bold")).pack(pady=20)
f7 = ctk.CTkFrame(page_converter, fg_color="transparent"); f7.pack(fill="x", padx=40)
entry_filepath_convert = ctk.CTkEntry(f7); entry_filepath_convert.pack(side="left", expand=True, fill="x", padx=5)
ctk.CTkButton(f7, text="Browse", command=browse_file_convert, width=80).pack(side="left")
lbl_stats_convert = ctk.CTkLabel(page_converter, text="", font=("Inter", 11), text_color="gray50"); lbl_stats_convert.pack()
f_btn_conv = ctk.CTkFrame(page_converter, fg_color="transparent"); f_btn_conv.pack(pady=10)
btn_run_convert = ctk.CTkButton(f_btn_conv, text="Convert Arrays to Strings", command=run_converter, font=("Inter", 14, "bold"), height=40); btn_run_convert.pack(side="left")
add_info_icon(f_btn_conv, "Select a CSV where some columns contain arrays (like [1, 2, 3])\nthat need to be cleaned up into readable strings.").pack(side="left", padx=5)
progress_convert = ctk.CTkProgressBar(page_converter, width=300, mode="indeterminate")

# --- UI: Date Harmonizer ---
page_dates = ctk.CTkFrame(content, fg_color="transparent"); page_dates.grid(row=0, column=0, sticky="nsew")
ctk.CTkLabel(page_dates, text="Date Harmonizer", font=("Inter", 24, "bold")).pack(pady=20)
f8 = ctk.CTkFrame(page_dates, fg_color="transparent"); f8.pack(fill="x", padx=40)
entry_filepath_dates = ctk.CTkEntry(f8); entry_filepath_dates.pack(side="left", expand=True, fill="x", padx=5)
ctk.CTkButton(f8, text="Browse", command=browse_file_dates, width=80).pack(side="left")
lbl_stats_dates = ctk.CTkLabel(page_dates, text="", font=("Inter", 11), text_color="gray50"); lbl_stats_dates.pack()

f_date_cols = ctk.CTkFrame(page_dates, fg_color="transparent"); f_date_cols.pack(fill="x", padx=40, pady=5)
entry_target_date_cols = ctk.CTkEntry(f_date_cols, placeholder_text="Columns to fix (split by ;)"); entry_target_date_cols.pack(side="left", expand=True, fill="x", padx=(0, 5))
combo_date_cols = ctk.CTkOptionMenu(f_date_cols, values=["Scan a file first..."], command=add_date_col_to_list, width=150); combo_date_cols.pack(side="left")
add_info_icon(f_date_cols, "The columns containing dates that need fixing (separated by ;).\nYou can pick them from the menu to add them quickly.").pack(side="left", padx=5)

f_pref = ctk.CTkFrame(page_dates, fg_color="transparent"); f_pref.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f_pref, text="Input Preference:").pack(side="left", padx=5)
combo_date_pref = ctk.CTkOptionMenu(f_pref, values=["US (MM/DD)", "EU (DD/MM)"], width=140); combo_date_pref.pack(side="left", padx=5)
add_info_icon(f_pref, "Helps distinguish ambiguous dates like 01/02.\nUS = Month/Day, EU = Day/Month.").pack(side="left", padx=5)

f_fmt = ctk.CTkFrame(page_dates, fg_color="transparent"); f_fmt.pack(fill="x", padx=40, pady=5)
ctk.CTkLabel(f_fmt, text="Target Format:     ").pack(side="left", padx=5)
combo_date_format = ctk.CTkOptionMenu(f_fmt, values=["YYYY-MM-DD (Snowflake)", "DD-MM-YYYY", "MM-DD-YYYY", "DD/MM/YYYY", "MM/DD/YYYY", "DD-MMM-YYYY (e.g. 15-Mar-2024)"], width=230); combo_date_format.pack(side="left", padx=5)
add_info_icon(f_fmt, "How you want the dates to appear in the final file.\nExample: YYYY-MM-DD is common in Snowflake .").pack(side="left", padx=5)

btn_run_dates = ctk.CTkButton(page_dates, text="Harmonize Dates", command=run_date_harmonizer, font=("Inter", 14, "bold"), height=40); btn_run_dates.pack(pady=10)
progress_dates = ctk.CTkProgressBar(page_dates, width=300); progress_dates.set(0)

# ==========================================
# SIDEBAR & NAV
# ==========================================
ctk.CTkLabel(sidebar, text="AIO Tools", font=("Inter", 20, "bold")).pack(pady=(20, 10))
def nav(page, btn):
    page.tkraise()
    for b in [bn1, bn2, bn3, bn4, bn5, bn6]: b.configure(fg_color="transparent")
    btn.configure(fg_color=("gray75", "gray25"))
bn1 = ctk.CTkButton(sidebar, text="CSV Splitter", command=lambda: nav(page_splitter, bn1), anchor="w", fg_color="transparent"); bn1.pack(fill="x", padx=10, pady=2)
bn2 = ctk.CTkButton(sidebar, text="Column Dropper", command=lambda: nav(page_dropper, bn2), anchor="w", fg_color="transparent"); bn2.pack(fill="x", padx=10, pady=2)
bn3 = ctk.CTkButton(sidebar, text="Array Converter", command=lambda: nav(page_converter, bn3), anchor="w", fg_color="transparent"); bn3.pack(fill="x", padx=10, pady=2)
bn4 = ctk.CTkButton(sidebar, text="CSV Concat", command=lambda: nav(page_concat, bn4), anchor="w", fg_color="transparent"); bn4.pack(fill="x", padx=10, pady=2)
bn5 = ctk.CTkButton(sidebar, text="Excel to CSV", command=lambda: nav(page_xlsx, bn5), anchor="w", fg_color="transparent"); bn5.pack(fill="x", padx=10, pady=2)
bn6 = ctk.CTkButton(sidebar, text="Date Harmonizer", command=lambda: nav(page_dates, bn6), anchor="w", fg_color="transparent"); bn6.pack(fill="x", padx=10, pady=2)
ctk.CTkLabel(sidebar, text=f"AIO {VERSION}", font=("Inter", 11), text_color="gray50").pack(side="bottom", pady=10)

# ==========================================
# DRAG & DROP
# ==========================================
def handle_drop_ext(event, entry):
    path = event.data
    if path.startswith('{') and path.endswith('}'): path = path[1:-1]
    entry.delete(0, "end"); entry.insert(0, path)
    if entry == entry_filepath_split: suggest_output_name(path, entry_output_name); update_stats_label(path, lbl_stats_split); load_splitter_columns(path)
    if entry == entry_filepath_drop: load_detected_columns(path); update_stats_label(path, lbl_stats_drop)
    if entry == entry_filepath_convert: update_stats_label(path, lbl_stats_convert)
    if entry == entry_folderpath_concat: suggest_output_name(path, entry_concat_output); load_folder_columns(path)
    if entry == entry_filepath_xlsx: load_excel_sheets(path); update_stats_label(path, lbl_stats_xlsx); suggest_output_name(path, entry_output_xlsx)
    if entry == entry_filepath_dates: load_date_columns(path); update_stats_label(path, lbl_stats_dates)

for e in [entry_filepath_split, entry_filepath_drop, entry_filepath_convert, entry_folderpath_concat, entry_filepath_xlsx, entry_filepath_dates]:
    e.drop_target_register(DND_FILES); e.dnd_bind('<<Drop>>', lambda ev, entry=e: handle_drop_ext(ev, entry))

add_standard_shortcuts(root)
# Bind Right-Click based on OS
root.bind_all("<Button-2>" if platform.system() == "Darwin" else "<Button-3>", show_context_menu)

if __name__ == "__main__":
    nav(page_splitter, bn1); root.mainloop()
