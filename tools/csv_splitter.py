import pandas as pd
import os

def _check_duplicates(df):
    """
    Check for ASSET_ID duplicates.
    Returns (cleaned_df, partial_dup_ids).
      - cleaned_df: DataFrame with true duplicates (identical across ALL columns) dropped.
      - partial_dup_ids: list of ASSET_ID values that are duplicated but differ in other columns.
        Empty list means no problematic duplicates remain.
    """
    if "ASSET_ID" not in df.columns:
        return df, []

    # Work only with rows where ASSET_ID is not null
    mask_not_null = df["ASSET_ID"].notna()
    df_with_id = df[mask_not_null]

    # Find ASSET_IDs that appear more than once
    dup_ids = df_with_id[df_with_id.duplicated(subset=["ASSET_ID"], keep=False)]["ASSET_ID"].unique()

    if len(dup_ids) == 0:
        return df, []

    # Drop true duplicates (identical across every column) — keep first occurrence
    df_deduped = df.drop_duplicates(keep="first")

    # After dropping true dups, check if any ASSET_IDs still appear more than once
    mask_not_null2 = df_deduped["ASSET_ID"].notna()
    df_with_id2 = df_deduped[mask_not_null2]
    remaining_dup_ids = (
        df_with_id2[df_with_id2.duplicated(subset=["ASSET_ID"], keep=False)]["ASSET_ID"]
        .unique()
        .tolist()
    )

    return df_deduped, remaining_dup_ids


def _find_dup_locations(generated_files, dup_ids):
    """
    Given the list of generated batch files and a set of duplicate ASSET_IDs,
    return a readable report showing which file(s) each duplicate ASSET_ID appears in.
    """
    id_to_files = {str(aid): [] for aid in dup_ids}

    for filepath in generated_files:
        batch_df = pd.read_csv(filepath)
        if "ASSET_ID" not in batch_df.columns:
            continue
        batch_name = os.path.basename(filepath)
        for aid in dup_ids:
            if aid in batch_df["ASSET_ID"].values:
                id_to_files[str(aid)].append(batch_name)

    lines = []
    for aid, files in id_to_files.items():
        if files:
            lines.append(f"ASSET_ID {aid} is a duplicate and exists in {' & '.join(files)}")
    return "\n".join(lines)


def process_split(input_file, output_name, rows_per_batch, progress_callback=None, completion_callback=None, error_callback=None):
    """
    Splits a CSV into batches.
    Runs in the background (or any thread calling it).
    Uses callbacks to notify the UI thread about events.
    """
    try:
        output_dir = os.path.dirname(input_file)
        generated_files = [] 
        
        df_original = pd.read_csv(input_file)

        # --- Duplicate check ---
        df_clean, partial_dup_ids = _check_duplicates(df_original)

        true_dups_dropped = len(df_original) - len(df_clean)
        # Use the cleaned DataFrame from here on
        df_original = df_clean
        
        df_test = df_original.iloc[:10]
        test_filename = os.path.join(output_dir, f"{output_name}_Test.csv")
        df_test.to_csv(test_filename, index=False)
        generated_files.append(test_filename)
        
        df_remaining = df_original.iloc[10:]
        total_remaining = len(df_remaining)
        num_batches = (total_remaining // rows_per_batch) + (1 if total_remaining % rows_per_batch != 0 else 0)
        
        for i in range(num_batches):
            start_idx = i * rows_per_batch
            end_idx = start_idx + rows_per_batch
            batch_df = df_remaining.iloc[start_idx:end_idx]
            
            batch_filename = os.path.join(output_dir, f"{output_name}_Batch{i+1}.csv")
            batch_df.to_csv(batch_filename, index=False)
            generated_files.append(batch_filename)
            
            if progress_callback:
                progress_callback(i + 1, num_batches)

        # --- Build result message ---
        parts = []

        if true_dups_dropped > 0:
            parts.append(f"Dropped {true_dups_dropped} true duplicate row(s) (identical across all columns).")

        if partial_dup_ids:
            dup_report = _find_dup_locations(generated_files, partial_dup_ids)
            parts.append(f"Duplicates found in input file: {', '.join(str(x) for x in partial_dup_ids)} ASSET_ID\n\n{dup_report}")

        # Validation
        df_total_reconstructed = pd.concat([pd.read_csv(f) for f in generated_files], ignore_index=True)
        
        if len(df_original) == len(df_total_reconstructed) and df_original.equals(df_total_reconstructed):
            parts.insert(0, f"Validation Passed!\nCreated {output_name}_Test.csv and {num_batches} batch files.")
            if completion_callback:
                completion_callback(True, "\n\n".join(parts))
        else:
            parts.insert(0, "Warning: The generated files do not perfectly match the original.")
            if completion_callback:
                completion_callback(False, "\n\n".join(parts))
            
    except Exception as e:
        if error_callback:
            error_callback(str(e))
