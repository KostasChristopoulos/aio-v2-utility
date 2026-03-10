import pandas as pd
import os

def get_sheet_names(filepath):
    """Returns a list of sheet names in an Excel file."""
    try:
        xl = pd.ExcelFile(filepath)
        return xl.sheet_names
    except Exception:
        return []

def process_xlsx_convert(input_file, sheet_name="All", on_complete=None, on_error=None):
    try:
        if sheet_name == "All":
            # Load all sheets
            dict_df = pd.read_excel(input_file, sheet_name=None)
            for s_name, df in dict_df.items():
                output_file = input_file.rsplit('.', 1)[0] + f"_{s_name}.csv"
                df.to_csv(output_file, index=False)
            on_complete(f"All sheets converted from {os.path.basename(input_file)}")
        else:
            # Load specific sheet
            df = pd.read_excel(input_file, sheet_name=sheet_name)
            output_file = input_file.rsplit('.', 1)[0] + f"_{sheet_name}.csv"
            df.to_csv(output_file, index=False)
            on_complete(output_file)
        
    except Exception as e:
        on_error(str(e))
