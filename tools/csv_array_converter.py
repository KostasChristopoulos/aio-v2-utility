import pandas as pd
import ast

def array_to_pipe(value):
    if isinstance(value, list):
        return "|".join(map(str, value))

    if isinstance(value, str):
        value_stripped = value.strip()
        if value_stripped.startswith("[") and value_stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(value_stripped)
                if isinstance(parsed, list):
                    return "|".join(map(str, parsed))
            except Exception:
                pass

    return value

def process_convert(input_file, on_complete, on_error):
    try:
        # Load the CSV
        df = pd.read_csv(input_file)
        
        # Apply the array_to_pipe function globally across the DataFrame
        # DataFrame.applymap is deprecated since pandas 2.1.0 in favor of DataFrame.map
        if hasattr(df, 'map'):
            df = df.map(array_to_pipe)
        else:
            df = df.applymap(array_to_pipe)  # Fallback for older pandas versions
        
        # Determine output filename
        output_file = input_file.replace('.csv', '_converted.csv')
        df.to_csv(output_file, index=False)
        
        on_complete(output_file)
        
    except Exception as e:
        on_error(str(e))
