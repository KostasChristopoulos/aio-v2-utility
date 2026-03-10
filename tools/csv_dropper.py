import pandas as pd

def process_drop(input_file, columns_raw, completion_callback=None, error_callback=None):
    """
    Drops columns from a CSV and saves it.
    Can be run in a background thread.
    """
    try:
        cols_to_drop = [col.strip() for col in columns_raw.split(';') if col.strip()]
        df = pd.read_csv(input_file)
        
        missing_cols = [col for col in cols_to_drop if col not in df.columns]
        warning_msg = None
        if missing_cols:
            warning_msg = f"These columns were not found in the CSV and will be skipped:\n{', '.join(missing_cols)}"
        
        df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
        df.to_csv(input_file, index=False)
        
        if completion_callback:
            completion_callback(len(cols_to_drop), warning_msg)
        
    except Exception as e:
        if error_callback:
            error_callback(str(e))
