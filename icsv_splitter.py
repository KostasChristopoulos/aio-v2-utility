import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import os
import threading
import subprocess
from datetime import datetime
from tkinterdnd2 import TkinterDnD, DND_FILES
import platform
from tkinter import Menu

# ==========================================
# CONFIG
# ==========================================
VERSION = "v1.4.0"
ENABLE_ACTIVITY_LOG = True 

# Global Log State
log_counts = {"warning": 0, "error": 0, "alert": 0}
log_minimized = False

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

def _check_duplicates(df, unique_col, drop_true_duplicates=True):
    if not unique_col or unique_col not in df.columns:
        if drop_true_duplicates:
            df_deduped = df.drop_duplicates(keep="first")
            return df_deduped, [], len(df) - len(df_deduped)
        return df, [], 0
    mask_not_null = df[unique_col].notna()
    df_with_id = df[mask_not_null]
    dup_ids = df_with_id[df_with_id.duplicated(subset=[unique_col], keep=False)][unique_col].unique()
    true_dups_count = 0
    if drop_true_duplicates:
        df_deduped = df.drop_duplicates(keep="first")
        true_dups_count = len(df) - len(df_deduped)
        df = df_deduped
    if len(dup_ids) == 0:
        return df, [], true_dups_count
    mask_not_null2 = df[unique_col].notna()
    df_with_id2 = df[mask_not_null2]
    remaining_dup_ids = (
        df_with_id2[df_with_id2.duplicated(subset=[unique_col], keep=False)][unique_col]
        .unique().tolist()
    )
    return df, remaining_dup_ids, true_dups_count

def _find_dup_locations(generated_files, dup_ids, unique_col):
    id_to_files = {str(aid): [] for aid in dup_ids}
    for filepath in generated_files:
        batch_df = pd.read_csv(filepath)
        if unique_col not in batch_df.columns: continue
        batch_name = os.path.basename(filepath)
        for aid in dup_ids:
            if aid in batch_df[unique_col].values:
                id_to_files[str(aid)].append(batch_name)
    lines = []
    for aid, files in id_to_files.items():
        if files: lines.append(f"ID {aid} ({unique_col}) is in: {' & '.join(files)}")
    return "\n".join(lines)

# ==========================================
# UI HELPERS
# ==========================================
def get_file_stats(filepath):
    try:
        df = pd.read_csv(filepath, nrows=0)
        cols = len(df.columns)
        row_count = sum(1 for _ in open(filepath)) - 1
        return f"{row_count:,} rows, {cols:,} columns"
    except Exception: return ""

def update_stats_label(filepath):
    stats = get_file_stats(filepath)
    lbl_stats.configure(text=stats if stats else "")

def suggest_output_name(input_path):
    base = os.path.basename(input_path).rsplit('.', 1)[0]
    entry_output_name.delete(0, "end"); entry_output_name.insert(0, base)

def open_folder(path):
    if os.path.exists(path):
        subprocess.run(['open', path if os.path.isdir(path) else os.path.dirname(path)])

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
        stats_text = f"Warnings: {log_counts['warning']} | Errors: {log_counts['error']}"
        lbl_log_stats.configure(text=stats_text)

def clear_log():
    if 'textbox_log' in globals():
        textbox_log.configure(state="normal")
        textbox_log.delete("1.0", "end"); textbox_log.configure(state="disabled")
        for k in log_counts: log_counts[k] = 0
        update_log_header_stats()
        log_message("Log cleared.", "info")

def save_log():
    if 'textbox_log' in globals():
        content = textbox_log.get("1.0", "end-1c")
        if not content.strip(): return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"split_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if file_path:
            with open(file_path, "w") as f: f.write(content)
            log_message(f"Log saved: {os.path.basename(file_path)}", "success")

def copy_log_line(event):
    if 'textbox_log' in globals():
        try:
            line_idx = textbox_log.index(f"@{event.x},{event.y}")
            line_start, line_end = f"{line_idx.split('.')[0]}.0", f"{line_idx.split('.')[0]}.end"
            content = textbox_log.get(line_start, line_end).strip()
            if content:
                root.clipboard_clear(); root.clipboard_append(content)
        except Exception: pass

def toggle_log():
    global log_minimized
    if log_minimized:
        log_frame.configure(height=130); btn_toggle_log.configure(text="▼"); log_minimized = False
    else:
        log_frame.configure(height=35); btn_toggle_log.configure(text="▲"); log_minimized = True

def add_standard_shortcuts(root):
    if platform.system() == "Darwin":
        root.bind_all("<Command-v>", lambda e: e.widget.event_generate("<<Paste>>"))
        root.bind_all("<Command-c>", lambda e: e.widget.event_generate("<<Copy>>"))
        root.bind_all("<Command-x>", lambda e: e.widget.event_generate("<<Cut>>"))
        root.bind_all("<Command-a>", lambda e: e.widget.event_generate("<<SelectAll>>"))

def show_context_menu(event):
    try:
        w = event.widget
        m = Menu(None, tearoff=0)
        m.add_command(label="Cut", command=lambda: w.event_generate("<<Cut>>"))
        m.add_command(label="Copy", command=lambda: w.event_generate("<<Copy>>"))
        m.add_command(label="Paste", command=lambda: w.event_generate("<<Paste>>"))
        m.add_separator()
        m.add_command(label="Select All", command=lambda: w.event_generate("<<SelectAll>>"))
        m.tk_popup(event.x_root, event.y_root)
    except Exception: pass

# ==========================================
# CORE BATCH PROCESS
# ==========================================
def browse_file():
    fn = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if fn:
        entry_filepath.delete(0, "end"); entry_filepath.insert(0, fn)
        suggest_output_name(fn); update_stats_label(fn)
        load_splitter_columns(fn)

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
    input_file = entry_filepath.get(); output_name = entry_output_name.get()
    unique_col = combo_unique_id.get()
    if unique_col == "(None)": unique_col = None
    create_test = check_test_split.get()
    drop_dups = check_drop_dups.get()
    try: rows_per_batch = int(entry_rows.get())
    except ValueError: messagebox.showerror("Error", "Check rows per batch number."); return
    if not input_file or not output_name: messagebox.showerror("Error", "Fill all fields."); return

    btn_run.configure(state="disabled", text="Processing...")
    progress_bar.set(0); progress_bar.pack(pady=5)

    def _process():
        try:
            output_dir = os.path.dirname(input_file); generated_files = []
            df_orig = pd.read_csv(input_file, low_memory=False)
            log_message(f"Loaded {len(df_orig)} rows.", "info")
            df_clean, partial_dup_ids, true_dups_dropped = _check_duplicates(df_orig, unique_col, drop_dups)
            # Reset index so it matches reconstructed batches
            df_clean = df_clean.reset_index(drop=True)
            
            create_test = check_test_split.get()
            if create_test:
                df_test = df_clean.iloc[:10]
                test_fn = os.path.join(output_dir, f"{output_name}_Test.csv")
                df_test.to_csv(test_fn, index=False); generated_files.append(test_fn)
                df_splitting = df_clean.iloc[10:]
            else:
                df_splitting = df_clean
            
            total_rows = len(df_splitting)
            num_batches = (total_rows // rows_per_batch) + (1 if total_rows % rows_per_batch != 0 else 0)
            for i in range(num_batches):
                chunk = df_splitting.iloc[i*rows_per_batch : (i+1)*rows_per_batch]
                batch_fn = os.path.join(output_dir, f"{output_name}_Batch{i+1}.csv")
                chunk.to_csv(batch_fn, index=False); generated_files.append(batch_fn)
                root.after(0, lambda pct=(i+1)/num_batches: progress_bar.set(pct))

            parts = []
            if true_dups_dropped > 0:
                parts.append(f"Dropped {true_dups_dropped} true duplicates.")
                log_message(f"Removed {true_dups_dropped} identical rows.", "warning")
            if partial_dup_ids:
                dup_report = _find_dup_locations(generated_files, partial_dup_ids, unique_col)
                parts.append(f"Duplicates found in IDs: {', '.join(str(x) for x in partial_dup_ids)}\n\n{dup_report}")
                log_message(f"Detected {len(partial_dup_ids)} problematic duplicates.", "warning")

            recon = pd.concat([pd.read_csv(f, low_memory=False) for f in generated_files], ignore_index=True)
            # Robust comparison ignoring dtypes
            content_match = False
            if len(df_clean) == len(recon):
                content_match = df_clean.astype(str).equals(recon.astype(str))
            
            if content_match:
                log_message("Validation Passed!", "success")
                test_msg = f"Created {output_name}_Test.csv and " if create_test else ""
                header = f"Split complete: {test_msg}{num_batches} batches created."
                if true_dups_dropped == 0:
                    header = f"Validation Passed!\n{header}"
                
                parts.insert(0, header)
                root.after(0, lambda: _on_done(True, "\n\n".join(parts), output_dir))
            else:
                log_message("Validation Failed!", "error")
                err_type = "cleaned data" if true_dups_dropped > 0 else "original file"
                root.after(0, lambda: _on_done(False, f"⚠️ WARNING: The generated batches do not match the {err_type}!", output_dir))
        except Exception as e:
            log_message(f"Error: {e}", "error")
            root.after(0, lambda: _on_done(False, str(e), None))

    def _on_done(success, msg, out_dir):
        btn_run.configure(state="normal", text="Run Splitter"); progress_bar.pack_forget()
        if success:
            messagebox.showinfo("Success!", msg)
            if out_dir:
                if hasattr(root, 'btn_open'): root.btn_open.destroy()
                root.btn_open = ctk.CTkButton(root, text="📁 Reveal in Finder", command=lambda: open_folder(out_dir), fg_color="transparent", border_width=1)
                root.btn_open.pack(pady=5)
        else: messagebox.showerror("Error", msg)

    log_message(f"Splitting {os.path.basename(input_file)}...", "info")
    threading.Thread(target=_process, daemon=True).start()

# ==========================================
# GUI SETUP
# ==========================================
class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

root = Tk()
root.title(f"CSV Splitter Pro {VERSION}")
root.geometry("600x520" if ENABLE_ACTIVITY_LOG else "600x320")

add_standard_shortcuts(root)
root.bind_all("<Button-2>" if platform.system() == "Darwin" else "<Button-3>", show_context_menu)

mf = ctk.CTkFrame(root, fg_color="transparent"); mf.pack(fill="x", padx=20, pady=20)
mf.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(mf, text="Input CSV:").grid(row=0, column=0, sticky="e", padx=5, pady=10)
entry_filepath = ctk.CTkEntry(mf); entry_filepath.grid(row=0, column=1, sticky="ew", padx=5)
ctk.CTkButton(mf, text="Browse", width=80, command=browse_file).grid(row=0, column=2, padx=5)
lbl_stats = ctk.CTkLabel(root, text="", font=("Inter", 11), text_color="gray50"); lbl_stats.pack(pady=(0, 10))

ctk.CTkLabel(mf, text="Rows/Batch:").grid(row=1, column=0, sticky="e", padx=5, pady=10)
entry_rows = ctk.CTkEntry(mf); entry_rows.insert(0, "5000"); entry_rows.grid(row=1, column=1, sticky="ew", padx=5)
add_info_icon(mf, "Number of rows per split file.").grid(row=1, column=2, sticky="w")

ctk.CTkLabel(mf, text="Output Base:").grid(row=2, column=0, sticky="e", padx=5, pady=10)
entry_output_name = ctk.CTkEntry(mf); entry_output_name.grid(row=2, column=1, sticky="ew", padx=5)
add_info_icon(mf, "The filename prefix for all generated batches.\nExample: 'MyReport' becomes 'MyReport_Batch1.csv'").grid(row=2, column=2, sticky="w")

ctk.CTkLabel(mf, text="Unique ID Col:").grid(row=3, column=0, sticky="e", padx=5, pady=10)
combo_unique_id = ctk.CTkOptionMenu(mf, values=["(None)"]); combo_unique_id.grid(row=3, column=1, sticky="ew", padx=5)
add_info_icon(mf, "Select a column containing unique identifiers (e.g., ASSET_ID).\nThe tool will check for duplicates within this column\nand report them back in window").grid(row=3, column=2, sticky="w")

check_test_split = ctk.BooleanVar(value=True)
check_drop_dups = ctk.BooleanVar(value=True)

f_opts = ctk.CTkFrame(root, fg_color="transparent"); f_opts.pack(pady=5)
chk_test = ctk.CTkCheckBox(f_opts, text="Create Test File (First 10 rows)?", variable=check_test_split, font=("Inter", 12))
chk_test.pack(side="left", padx=2)
add_info_icon(f_opts, "Creates a small 10-row file titled '_Test.csv' to verify your delivery template.").pack(side="left", padx=(0, 15))

chk_drop = ctk.CTkCheckBox(f_opts, text="Drop True Duplicates?", variable=check_drop_dups, font=("Inter", 12))
chk_drop.pack(side="left", padx=2)
add_info_icon(f_opts, "True Duplicate: A row that is 100% identical to another across ALL columns.\nIf this is ON these rows will be dropped automatically").pack(side="left", padx=5)

btn_run = ctk.CTkButton(root, text="Run Splitter", command=run_splitter, font=("Inter", 14, "bold"), height=40); btn_run.pack(pady=10)
progress_bar = ctk.CTkProgressBar(root, width=300); progress_bar.set(0)

if ENABLE_ACTIVITY_LOG:
    log_frame = ctk.CTkFrame(root, height=130, corner_radius=0); log_frame.pack(fill="both", expand=True, padx=10, pady=10)
    log_frame.pack_propagate(False)
    lh = ctk.CTkFrame(log_frame, fg_color="transparent", height=30); lh.pack(fill="x", padx=10, pady=2)
    btn_toggle_log = ctk.CTkButton(lh, text="▼", width=25, height=20, command=toggle_log, fg_color="transparent"); btn_toggle_log.pack(side="left")
    ctk.CTkLabel(lh, text="Activity Log", font=("Inter", 12, "bold")).pack(side="left", padx=5)
    lbl_log_stats = ctk.CTkLabel(lh, text="Warnings: 0 | Errors: 0", font=("Inter", 11), text_color="gray50"); lbl_log_stats.pack(side="left", padx=15)
    ctk.CTkButton(lh, text="Clear", width=45, height=20, font=("Inter", 10), command=clear_log, fg_color="transparent", border_width=1).pack(side="right", padx=2)
    ctk.CTkButton(lh, text="Save", width=45, height=20, font=("Inter", 10), command=save_log, fg_color="transparent", border_width=1).pack(side="right", padx=2)
    textbox_log = ctk.CTkTextbox(log_frame, font=("Courier", 11)); textbox_log.pack(fill="both", expand=True, padx=10, pady=(0, 5))
    textbox_log.bind("<Double-Button-1>", copy_log_line)
    textbox_log.tag_config("timestamp", foreground="#888888")
    textbox_log.tag_config("info", foreground="#AAB0B8")
    textbox_log.tag_config("success", foreground="#2ECC71")
    textbox_log.tag_config("warning", foreground="#F1C40F")
    textbox_log.tag_config("error", foreground="#E74C3C")
    textbox_log.configure(state="disabled")
    log_message("Ready.", "info")

# Drag & Drop
def h_drop(e):
    p = e.data
    if p.startswith('{') and p.endswith('}'): p = p[1:-1]
    entry_filepath.delete(0, "end"); entry_filepath.insert(0, p)
    suggest_output_name(p); update_stats_label(p); load_splitter_columns(p)
entry_filepath.drop_target_register(DND_FILES); entry_filepath.dnd_bind('<<Drop>>', h_drop)

root.mainloop()