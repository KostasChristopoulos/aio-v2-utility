import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import json
from datetime import datetime
from PIL import Image, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES

from tools.csv_splitter import process_split
from tools.csv_dropper import process_drop
from tools.csv_array_converter import process_convert
from tools.csv_concat import process_concat

# ==========================================
# 1. CORE APP SETUP & NAVIGATION
# ==========================================
VERSION = "v2.0.0"
ENABLE_ACTIVITY_LOG = True  # Set to False to disable the log UI easily at the bottom
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

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
root.title("AIO v2")
root.geometry("700x500")

# Add Icon
icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
if os.path.exists(icon_path):
    icon_image = ImageTk.PhotoImage(Image.open(icon_path))
    root.iconphoto(True, icon_image)

def show_page(page_frame):
    page_frame.tkraise()

def log_message(msg):
    # Print to standard output as well
    print(msg)
    # Check if the UI feature is enabled and the log widget exists
    if ENABLE_ACTIVITY_LOG and 'textbox_log' in globals():
        timestamp = datetime.now().strftime("%H:%M:%S")
        def _insert():
            textbox_log.configure(state="normal")
            textbox_log.insert("end", f"[{timestamp}] {msg}\n")
            textbox_log.see("end")
            textbox_log.configure(state="disabled")
        root.after(0, _insert)

# ==========================================
# 2. LOGIC: CSV SPLITTER
# ==========================================
def browse_file_split():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        entry_filepath_split.delete(0, "end")
        entry_filepath_split.insert(0, filename)

def run_splitter():
    input_file = entry_filepath_split.get()
    output_name = entry_output_name.get()
    
    try:
        rows_per_batch = int(entry_rows.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for rows per batch.")
        return

    if not input_file or not output_name:
        messagebox.showerror("Error", "Please make sure all fields are filled out.")
        return
        
    # Disable button to indicate it's running
    btn_run_split.configure(state="disabled", text="Processing...")
    progress_split.set(0)
    progress_split.pack(pady=10)

    # Define our callbacks for the background thread results
    def on_progress(current, total):
        if total > 0:
            pct = current / total
            root.after(0, lambda: progress_split.set(pct))
        
    def on_complete(success, message):
        def ui_update():
            btn_run_split.configure(state="normal", text="Run Splitter")
            progress_split.pack_forget()
            if success:
                log_message(message)
                messagebox.showinfo("Success!", message)
            else:
                log_message(f"Validation Failed: {message}")
                messagebox.showwarning("Validation Failed", message)
        root.after(0, ui_update)
            
    def on_error(error_msg):
        def ui_error():
            btn_run_split.configure(state="normal", text="Run Splitter")
            progress_split.pack_forget()
            log_message(f"Error: {error_msg}")
            messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
        root.after(0, ui_error)

    log_message(f"Started splitting {os.path.basename(input_file)} into batches of {rows_per_batch}...")
    
    # Save parameters to configuration memory
    cfg = load_config()
    cfg["split_input_file"] = input_file
    cfg["split_output_name"] = output_name
    cfg["split_rows"] = rows_per_batch
    save_config(cfg)

    # Start the data processing in a separate thread (Feature A)
    # This keeps the UI responsive!
    thread = threading.Thread(target=process_split, args=(
        input_file, output_name, rows_per_batch, 
        on_progress, on_complete, on_error
    ))
    thread.daemon = True
    thread.start()

# ==========================================
# 3. LOGIC: COLUMN DROPPER
# ==========================================
def browse_file_drop():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        entry_filepath_drop.delete(0, "end")
        entry_filepath_drop.insert(0, filename)

def run_dropper():
    input_file = entry_filepath_drop.get()
    columns_raw = entry_columns.get()
    
    if not input_file or not columns_raw:
        messagebox.showerror("Error", "Please provide a file path and at least one column name.")
        return
        
    btn_run_drop.configure(state="disabled", text="Processing...")
    progress_drop.pack(pady=10)
    progress_drop.start()
    
    def on_complete(num_dropped, warning_msg):
        def ui_update():
            progress_drop.stop()
            progress_drop.pack_forget()
            btn_run_drop.configure(state="normal", text="Drop & Save")
            if warning_msg:
                log_message(f"Warning: {warning_msg}")
                messagebox.showwarning("Warning", warning_msg)
            
            success_msg = f"Successfully targeted {num_dropped} column(s) and updated the file."
            log_message(success_msg)
            messagebox.showinfo("Success!", success_msg)
        root.after(0, ui_update)
        
    def on_error(error_msg):
        def ui_error():
            progress_drop.stop()
            progress_drop.pack_forget()
            btn_run_drop.configure(state="normal", text="Drop & Save")
            log_message(f"Error: {error_msg}")
            messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
        root.after(0, ui_error)
        
    log_message(f"Started dropping columns '{columns_raw}' from {os.path.basename(input_file)}...")
    
    # Save parameters to configuration memory
    cfg = load_config()
    cfg["drop_input_file"] = input_file
    cfg["drop_columns"] = columns_raw
    save_config(cfg)

    # Start the data processing in a separate thread (Feature A)
    thread = threading.Thread(target=process_drop, args=(
        input_file, columns_raw, on_complete, on_error
    ))
    thread.daemon = True
    thread.start()

# ==========================================
# 4. LOGIC: ARRAY CONVERTER
# ==========================================
def browse_file_convert():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        entry_filepath_convert.delete(0, "end")
        entry_filepath_convert.insert(0, filename)

def run_converter():
    input_file = entry_filepath_convert.get()
    
    if not input_file:
        messagebox.showerror("Error", "Please provide a file path.")
        return
        
    btn_run_convert.configure(state="disabled", text="Processing...")
    progress_convert.pack(pady=10)
    progress_convert.start()
    
    def on_complete(output_file):
        def ui_update():
            progress_convert.stop()
            progress_convert.pack_forget()
            btn_run_convert.configure(state="normal", text="Convert Arrays to Strings")
            
            success_msg = f"Successfully converted arrays and saved to:\n{os.path.basename(output_file)}"
            log_message(success_msg)
            messagebox.showinfo("Success!", success_msg)
        root.after(0, ui_update)
        
    def on_error(error_msg):
        def ui_error():
            progress_convert.stop()
            progress_convert.pack_forget()
            btn_run_convert.configure(state="normal", text="Convert Arrays to Strings")
            log_message(f"Error: {error_msg}")
            messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
        root.after(0, ui_error)
        
    log_message(f"Started converting arrays to strings for {os.path.basename(input_file)}...")
    
    # Save parameters to configuration memory
    cfg = load_config()
    cfg["convert_input_file"] = input_file
    save_config(cfg)

    # Start the data processing in a separate thread
    thread = threading.Thread(target=process_convert, args=(
        input_file, on_complete, on_error
    ))
    thread.daemon = True
    thread.start()

# ==========================================
# 5. LOGIC: CSV CONCAT
# ==========================================
def browse_folder_concat():
    foldername = filedialog.askdirectory()
    if foldername:
        entry_folderpath_concat.delete(0, "end")
        entry_folderpath_concat.insert(0, foldername)

def run_concat():
    folder_path = entry_folderpath_concat.get()
    output_name = entry_concat_output.get()
    
    if not folder_path:
        messagebox.showerror("Error", "Please provide a folder path.")
        return
    if not output_name:
        messagebox.showerror("Error", "Please provide an output file name.")
        return
        
    btn_run_concat.configure(state="disabled", text="Processing...")
    progress_concat.set(0)
    progress_concat.pack(pady=10)
    
    def on_progress(current, total):
        if total > 0:
            pct = current / total
            root.after(0, lambda: progress_concat.set(pct))
    
    def on_complete(success, message):
        def ui_update():
            btn_run_concat.configure(state="normal", text="Concatenate")
            progress_concat.pack_forget()
            if success:
                log_message(message)
                messagebox.showinfo("Success!", message)
            else:
                log_message(f"Validation Failed: {message}")
                messagebox.showwarning("Validation Failed", message)
        root.after(0, ui_update)
        
    def on_error(error_msg):
        def ui_error():
            btn_run_concat.configure(state="normal", text="Concatenate")
            progress_concat.pack_forget()
            log_message(f"Error: {error_msg}")
            messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
        root.after(0, ui_error)
        
    log_message(f"Started concatenating CSVs from {folder_path}...")
    
    cfg = load_config()
    cfg["concat_folder"] = folder_path
    cfg["concat_output"] = output_name
    save_config(cfg)

    thread = threading.Thread(target=process_concat, args=(
        folder_path, output_name, on_progress, on_complete, on_error
    ))
    thread.daemon = True
    thread.start()

# ==========================================
# 6. BUILD THE LAYOUT AREAS
# ==========================================
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

sidebar = ctk.CTkFrame(root, width=160, corner_radius=0)
sidebar.grid(row=0, column=0, sticky="nsew")

content = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent")
content.grid(row=0, column=1, sticky="nsew")
content.grid_rowconfigure(0, weight=1)
content.grid_columnconfigure(0, weight=1)

if ENABLE_ACTIVITY_LOG:
    content.grid_rowconfigure(1, weight=0)
    log_frame = ctk.CTkFrame(content, height=130, corner_radius=0)
    log_frame.grid(row=1, column=0, sticky="ew")
    log_frame.pack_propagate(False)
    
    log_label = ctk.CTkLabel(log_frame, text="Activity Log", font=("Inter", 12, "bold"))
    log_label.pack(anchor="w", padx=10, pady=(5, 0))
    
    textbox_log = ctk.CTkTextbox(log_frame, font=("Courier", 11))
    textbox_log.pack(fill="both", expand=True, padx=10, pady=5)
    textbox_log.configure(state="disabled")
    log_message("Application initialized.")

page_splitter = ctk.CTkFrame(content, corner_radius=0, fg_color="transparent")
page_splitter.grid(row=0, column=0, sticky="nsew")

page_dropper = ctk.CTkFrame(content, corner_radius=0, fg_color="transparent")
page_dropper.grid(row=0, column=0, sticky="nsew")

page_converter = ctk.CTkFrame(content, corner_radius=0, fg_color="transparent")
page_converter.grid(row=0, column=0, sticky="nsew")

page_concat = ctk.CTkFrame(content, corner_radius=0, fg_color="transparent")
page_concat.grid(row=0, column=0, sticky="nsew")

# ==========================================
# 7. POPULATE PAGE 1: SPLITTER
# ==========================================
ctk.CTkLabel(page_splitter, text="CSV Batch Splitter", font=("Inter", 24, "bold")).pack(pady=(30, 20))

frame_file_split = ctk.CTkFrame(page_splitter, fg_color="transparent")
frame_file_split.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_file_split, text="Select CSV:", width=120, anchor="e").pack(side="left", padx=(0, 10))
entry_filepath_split = ctk.CTkEntry(frame_file_split)
entry_filepath_split.pack(side="left", padx=(0, 10), expand=True, fill="x")
ctk.CTkButton(frame_file_split, text="Browse", command=browse_file_split, width=80).pack(side="left")

frame_rows = ctk.CTkFrame(page_splitter, fg_color="transparent")
frame_rows.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_rows, text="Rows per batch:", width=120, anchor="e").pack(side="left", padx=(0, 10))
entry_rows = ctk.CTkEntry(frame_rows)
entry_rows.insert(0, "5000")
entry_rows.pack(side="left", fill="x", expand=True)

frame_output = ctk.CTkFrame(page_splitter, fg_color="transparent")
frame_output.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_output, text="Output Base Name:", width=120, anchor="e").pack(side="left", padx=(0, 10))
entry_output_name = ctk.CTkEntry(frame_output)
entry_output_name.insert(0, "Your_File_Name")
entry_output_name.pack(side="left", fill="x", expand=True)

btn_run_split = ctk.CTkButton(page_splitter, text="Run Splitter", command=run_splitter, font=("Inter", 14, "bold"), height=40)
btn_run_split.pack(pady=(30, 20))

progress_split = ctk.CTkProgressBar(page_splitter, width=300)
progress_split.set(0)

# ==========================================
# 8. POPULATE PAGE 2: COLUMN DROPPER
# ==========================================
ctk.CTkLabel(page_dropper, text="CSV Column Dropper", font=("Inter", 24, "bold")).pack(pady=(30, 20))

frame_file_drop = ctk.CTkFrame(page_dropper, fg_color="transparent")
frame_file_drop.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_file_drop, text="Select CSV:", width=120, anchor="e").pack(side="left", padx=(0, 10))
entry_filepath_drop = ctk.CTkEntry(frame_file_drop)
entry_filepath_drop.pack(side="left", padx=(0, 10), expand=True, fill="x")
ctk.CTkButton(frame_file_drop, text="Browse", command=browse_file_drop, width=80).pack(side="left")

frame_columns = ctk.CTkFrame(page_dropper, fg_color="transparent")
frame_columns.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_columns, text="Columns to drop (separate by ;):", width=200, anchor="e").pack(side="left", padx=(0, 10))
entry_columns = ctk.CTkEntry(frame_columns)
entry_columns.pack(side="left", expand=True, fill="x")

ctk.CTkLabel(page_dropper, text="Warning: This will overwrite the original file.", text_color="red").pack(pady=(15, 5))
btn_run_drop = ctk.CTkButton(page_dropper, text="Drop & Save", command=run_dropper, fg_color="#28a745", hover_color="#218838", font=("Inter", 14, "bold"), height=40)
btn_run_drop.pack(pady=(10, 20))

progress_drop = ctk.CTkProgressBar(page_dropper, width=300, mode="indeterminate")

# ==========================================
# 9. POPULATE PAGE 3: ARRAY CONVERTER
# ==========================================
ctk.CTkLabel(page_converter, text="Array to String Converter", font=("Inter", 24, "bold")).pack(pady=(30, 20))

frame_file_convert = ctk.CTkFrame(page_converter, fg_color="transparent")
frame_file_convert.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_file_convert, text="Select CSV:", width=120, anchor="e").pack(side="left", padx=(0, 10))
entry_filepath_convert = ctk.CTkEntry(frame_file_convert)
entry_filepath_convert.pack(side="left", padx=(0, 10), expand=True, fill="x")
ctk.CTkButton(frame_file_convert, text="Browse", command=browse_file_convert, width=80).pack(side="left")

ctk.CTkLabel(page_converter, text="Finds arrays inside all cells e.g. ['A', 'B']\nand converts them to pipe-delimited strings 'A|B'.\n\nSaves automatically as: original_name_converted.csv", text_color="gray70", justify="center").pack(pady=(20, 20))

btn_run_convert = ctk.CTkButton(page_converter, text="Convert Arrays to Strings", command=run_converter, font=("Inter", 14, "bold"), height=40)
btn_run_convert.pack(pady=(10, 20))

progress_convert = ctk.CTkProgressBar(page_converter, width=300, mode="indeterminate")

# ==========================================
# 10. POPULATE PAGE 4: CSV CONCAT
# ==========================================
ctk.CTkLabel(page_concat, text="CSV Concatenator", font=("Inter", 24, "bold")).pack(pady=(30, 20))

frame_folder_concat = ctk.CTkFrame(page_concat, fg_color="transparent")
frame_folder_concat.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_folder_concat, text="Select Folder:", width=120, anchor="e").pack(side="left", padx=(0, 10))
entry_folderpath_concat = ctk.CTkEntry(frame_folder_concat)
entry_folderpath_concat.pack(side="left", padx=(0, 10), expand=True, fill="x")
ctk.CTkButton(frame_folder_concat, text="Browse", command=browse_folder_concat, width=80).pack(side="left")

frame_concat_output = ctk.CTkFrame(page_concat, fg_color="transparent")
frame_concat_output.pack(pady=10, fill="x", padx=40)
ctk.CTkLabel(frame_concat_output, text="Output File Name:", width=120, anchor="e").pack(side="left", padx=(0, 10))
entry_concat_output = ctk.CTkEntry(frame_concat_output)
entry_concat_output.insert(0, "combined")
entry_concat_output.pack(side="left", fill="x", expand=True)

ctk.CTkLabel(page_concat, text="Finds all .csv files in the selected folder\nand concatenates them into a single CSV.\n\nSaves as: <output_name>.csv inside the same folder.", text_color="gray70", justify="center").pack(pady=(20, 20))

btn_run_concat = ctk.CTkButton(page_concat, text="Concatenate", command=run_concat, font=("Inter", 14, "bold"), height=40)
btn_run_concat.pack(pady=(10, 20))

progress_concat = ctk.CTkProgressBar(page_concat, width=300)
progress_concat.set(0)

# ==========================================
# 11. SIDEBAR NAVIGATION BUTTONS
# ==========================================
ctk.CTkLabel(sidebar, text="Tools", font=("Inter", 18, "bold")).pack(pady=(30, 20))

def update_sidebar_buttons(active_btn):
    for btn in [btn_nav_split, btn_nav_drop, btn_nav_convert, btn_nav_concat]:
        btn.configure(fg_color="gray75" if ctk.get_appearance_mode() == "Light" else "gray25" if btn == active_btn else "transparent")

def nav_split():
    show_page(page_splitter)
    update_sidebar_buttons(btn_nav_split)

def nav_drop():
    show_page(page_dropper)
    update_sidebar_buttons(btn_nav_drop)

def nav_convert():
    show_page(page_converter)
    update_sidebar_buttons(btn_nav_convert)

def nav_concat():
    show_page(page_concat)
    update_sidebar_buttons(btn_nav_concat)

btn_nav_split = ctk.CTkButton(sidebar, text="CSV Splitter", command=nav_split, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", height=40, font=("Inter", 13))
btn_nav_split.pack(pady=5, padx=10, fill="x")

btn_nav_drop = ctk.CTkButton(sidebar, text="Column Dropper", command=nav_drop, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", height=40, font=("Inter", 13))
btn_nav_drop.pack(pady=5, padx=10, fill="x")

btn_nav_convert = ctk.CTkButton(sidebar, text="Array Converter", command=nav_convert, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", height=40, font=("Inter", 13))
btn_nav_convert.pack(pady=5, padx=10, fill="x")

btn_nav_concat = ctk.CTkButton(sidebar, text="CSV Concat", command=nav_concat, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", height=40, font=("Inter", 13))
btn_nav_concat.pack(pady=5, padx=10, fill="x")

# Version Label at the bottom
version_label = ctk.CTkLabel(sidebar, text=f"AIO {VERSION}", font=("Inter", 11), text_color="gray50")
version_label.pack(side="bottom", pady=10)

# ==========================================
# 12. POST-INIT: DND BINDINGS & CONFIG LOAD
# ==========================================
def handle_drop(event, entry_widget):
    filepath = event.data
    # tkinterdnd2 on Mac sometimes wraps paths containing spaces in curly braces
    if filepath.startswith('{') and filepath.endswith('}'):
        filepath = filepath[1:-1]
    entry_widget.delete(0, "end")
    entry_widget.insert(0, filepath)

entry_filepath_split.drop_target_register(DND_FILES)
entry_filepath_split.dnd_bind('<<Drop>>', lambda e: handle_drop(e, entry_filepath_split))

entry_filepath_drop.drop_target_register(DND_FILES)
entry_filepath_drop.dnd_bind('<<Drop>>', lambda e: handle_drop(e, entry_filepath_drop))

entry_filepath_convert.drop_target_register(DND_FILES)
entry_filepath_convert.dnd_bind('<<Drop>>', lambda e: handle_drop(e, entry_filepath_convert))

entry_folderpath_concat.drop_target_register(DND_FILES)
entry_folderpath_concat.dnd_bind('<<Drop>>', lambda e: handle_drop(e, entry_folderpath_concat))

# Pre-load Config (Persistent Memory)
cfg = load_config()
if cfg.get("split_input_file"):
    entry_filepath_split.delete(0, "end")
    entry_filepath_split.insert(0, cfg["split_input_file"])
if cfg.get("split_output_name"):
    entry_output_name.delete(0, "end")
    entry_output_name.insert(0, cfg["split_output_name"])
if cfg.get("split_rows"):
    entry_rows.delete(0, "end")
    entry_rows.insert(0, str(cfg["split_rows"]))
if cfg.get("drop_input_file"):
    entry_filepath_drop.delete(0, "end")
    entry_filepath_drop.insert(0, cfg["drop_input_file"])
if cfg.get("drop_columns"):
    entry_columns.delete(0, "end")
    entry_columns.insert(0, cfg["drop_columns"])
if cfg.get("convert_input_file"):
    entry_filepath_convert.delete(0, "end")
    entry_filepath_convert.insert(0, cfg["convert_input_file"])
if cfg.get("concat_folder"):
    entry_folderpath_concat.delete(0, "end")
    entry_folderpath_concat.insert(0, cfg["concat_folder"])
if cfg.get("concat_output"):
    entry_concat_output.delete(0, "end")
    entry_concat_output.insert(0, cfg["concat_output"])

if __name__ == "__main__":
    nav_split()
    root.mainloop()
