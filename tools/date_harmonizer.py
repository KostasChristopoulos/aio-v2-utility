import pandas as pd
import os

def process_date_harmonization(input_file, target_columns, input_preference, output_format, progress_callback=None, completion_callback=None, error_callback=None):
    """
    input_preference: 'US' (monthfirst) or 'EU' (dayfirst)
    output_format: str (strftime compatible)
    """
    try:
        df = pd.read_csv(input_file)
        total_cols = len(target_columns)
        err_report = []
        
        day_first = True if input_preference == 'EU' else False
        
        for i, col in enumerate(target_columns):
            if col not in df.columns:
                continue
            
            # Convert to datetime objects
            # errors='coerce' turns unparseable dates into NaT
            original_series = df[col].copy()
            df[col] = pd.to_datetime(df[col], dayfirst=day_first, errors='coerce')
            
            # Find NaT values that weren't originally null
            failed_mask = df[col].isna() & original_series.notna()
            failed_indices = df.index[failed_mask].tolist()
            
            if failed_indices:
                err_report.append(f"Column '{col}': Failed to parse {len(failed_indices)} rows (e.g., row {failed_indices[0]+1})")
            
            # Format back to string
            # We use dt.strftime but keep NaT as empty strings or original values? 
            # Better to show as empty/NaT to flag the error.
            df[col] = df[col].dt.strftime(output_format).fillna("")
            
            if progress_callback:
                progress_callback(i + 1, total_cols)

        # Save output
        output_dir = os.path.dirname(input_file)
        base_name = os.path.basename(input_file).rsplit('.', 1)[0]
        output_file = os.path.join(output_dir, f"{base_name}_dates_fixed.csv")
        df.to_csv(output_file, index=False)
        
        if completion_callback:
            msg = f"Successfully harmonized dates in {output_file}."
            if err_report:
                msg += "\n\nIssues encountered:\n" + "\n".join(err_report)
            completion_callback(True, msg, output_file)
            
    except Exception as e:
        if error_callback:
            error_callback(str(e))
