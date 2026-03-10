import pandas as pd
import os
import glob

def get_common_columns(folder_path):
    """
    Scans CSVs in folder. Returns:
    - common_cols: list of ALL CAPS column names found in ALL files.
    - disconnected_files: list of files that have no columns in common with the majority.
    """
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not csv_files:
        return [], []

    file_to_cols = {}
    for f in csv_files:
        try:
            df = pd.read_csv(f, nrows=1)
            file_to_cols[os.path.basename(f)] = set(c.upper() for c in df.columns)
        except:
            continue

    if not file_to_cols:
        return [], []

    # Find columns present in ALL files
    list_of_sets = list(file_to_cols.values())
    common_set = set.intersection(*list_of_sets) if list_of_sets else set()
    
    # Identify files that have zero intersection with the union of others (disconnected)
    disconnected = []
    all_files = list(file_to_cols.keys())
    for f_name in all_files:
        others_union = set().union(*(file_to_cols[o] for o in all_files if o != f_name))
        if others_union and not (file_to_cols[f_name] & others_union):
            disconnected.append(f_name)

    return sorted(list(common_set)), disconnected

def process_concat(folder_path, output_name, target_column=None, progress_callback=None, completion_callback=None, error_callback=None):
    try:
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        if not csv_files:
            if error_callback: error_callback("No CSV files found in the selected folder.")
            return

        # Phase 1: Global Column Frequency Scan
        col_global_counts = {}
        file_schemas = {} # Map filename -> actual col names
        for f in csv_files:
            try:
                df_head = pd.read_csv(f, nrows=1)
                file_schemas[f] = df_head.columns.tolist()
                for c in df_head.columns:
                    uname = c.upper()
                    col_global_counts[uname] = col_global_counts.get(uname, 0) + 1
            except:
                continue

        all_dfs = []
        total_files = len(csv_files)

        for i, f in enumerate(csv_files):
            df = pd.read_csv(f)
            fname = os.path.basename(f)
            
            # --- Drop unique NULL columns ---
            if not target_column:
                cols_to_drop = []
                for col in df.columns:
                    uname = col.upper()
                    # Is it unique to this file?
                    if col_global_counts.get(uname) == 1:
                        # Is it entirely NULL?
                        if df[col].isnull().all():
                            cols_to_drop.append(col)
                            if completion_callback: # Use as log conduit
                                completion_callback(False, f"LOG: Column '{col}' from '{fname}' is NULL and unique and will be dropped.")
                
                if cols_to_drop:
                    df = df.drop(columns=cols_to_drop)

            # --- Target Column Logic ---
            if target_column:
                matched_col = None
                for col in df.columns:
                    if col.upper() == target_column.upper():
                        matched_col = col
                        break
                
                if matched_col:
                    df = df[[matched_col]]
                    df.columns = [target_column.upper()]
                else:
                    continue 

            all_dfs.append(df)
            if progress_callback:
                progress_callback(i + 1, total_files)

        if not all_dfs:
            if error_callback: error_callback(f"No files could be processed.")
            return

        combined_df = pd.concat(all_dfs, ignore_index=True)
        output_path = os.path.join(folder_path, f"{output_name}.csv")
        combined_df.to_csv(output_path, index=False)

        if completion_callback:
            msg = f"Successfully concatenated {len(all_dfs)} files.\n\nSaved to: {output_path}"
            completion_callback(True, msg)

    except Exception as e:
        if error_callback:
            error_callback(str(e))
