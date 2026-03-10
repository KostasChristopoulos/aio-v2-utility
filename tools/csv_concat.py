import pandas as pd
import os
import glob

def process_concat(folder_path, output_name, on_progress, on_complete, on_error):
    try:
        # Find all CSV files in the folder
        csv_files = sorted(glob.glob(os.path.join(folder_path, "*.csv")))
        
        if not csv_files:
            on_complete(False, "No CSV files found in the specified folder.")
            return
        
        total = len(csv_files)
        frames = []
        
        for i, filepath in enumerate(csv_files, 1):
            df = pd.read_csv(filepath)
            frames.append(df)
            on_progress(i, total)
        
        # Concatenate all DataFrames
        combined = pd.concat(frames, ignore_index=True)
        
        # Build the output path (save inside the same folder)
        output_file = os.path.join(folder_path, f"{output_name}.csv")
        combined.to_csv(output_file, index=False)
        
        on_complete(True, f"Concatenated {total} CSV file(s) ({len(combined)} total rows) into:\n{os.path.basename(output_file)}")
        
    except Exception as e:
        on_error(str(e))
