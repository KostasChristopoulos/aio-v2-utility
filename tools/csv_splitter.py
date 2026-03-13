import pandas as pd
import os

def _check_duplicates(df, unique_col, drop_true_duplicates=True):
    """
    Check for duplicates in a user-specified unique column.
    Returns (cleaned_df, partial_dup_ids, true_dups_dropped_count).
    """
    if not unique_col or unique_col not in df.columns:
        # Still check for true duplicates if requested
        if drop_true_duplicates:
            df_deduped = df.drop_duplicates(keep="first")
            return df_deduped, [], len(df) - len(df_deduped)
        return df, [], 0

    # Work only with rows where unique_col is not null
    mask_not_null = df[unique_col].notna()
    df_with_id = df[mask_not_null]

    # Find IDs that appear more than once
    dup_ids = df_with_id[df_with_id.duplicated(subset=[unique_col], keep=False)][unique_col].unique()

    true_dups_count = 0
    if drop_true_duplicates:
        df_deduped = df.drop_duplicates(keep="first")
        true_dups_count = len(df) - len(df_deduped)
        df = df_deduped

    if len(dup_ids) == 0:
        return df, [], true_dups_count

    # After dropping true dups (if requested), check if any IDs still appear more than once
    mask_not_null2 = df[unique_col].notna()
    df_with_id2 = df[mask_not_null2]
    remaining_dup_ids = (
        df_with_id2[df_with_id2.duplicated(subset=[unique_col], keep=False)][unique_col]
        .unique()
        .tolist()
    )

    return df, remaining_dup_ids, true_dups_count


def _find_dup_locations(generated_files, dup_ids, unique_col):
    """
    Given the list of generated batch files and a set of duplicate IDs,
    return a report showing which file(s) each duplicate ID appears in.
    """
    id_to_files = {str(aid): [] for aid in dup_ids}

    for filepath in generated_files:
        batch_df = pd.read_csv(filepath)
        if unique_col not in batch_df.columns:
            continue
        batch_name = os.path.basename(filepath)
        for aid in dup_ids:
            if aid in batch_df[unique_col].values:
                id_to_files[str(aid)].append(batch_name)

    lines = []
    for aid, files in id_to_files.items():
        if files:
            lines.append(f"ID {aid} ({unique_col}) is a duplicate and exists in {' & '.join(files)}")
    return "\n".join(lines)


def process_split(input_file, output_name, rows_per_batch, unique_col=None, create_test_file=True, progress_callback=None, completion_callback=None, error_callback=None, drop_true_duplicates=True):
    """
    Splits a CSV into batches.
    """
    try:
        output_dir = os.path.dirname(input_file)
        generated_files = [] 
        
        # Using low_memory=False to avoid DtypeWarning on varied data
        df_original = pd.read_csv(input_file, low_memory=False)

        # --- Duplicate check using dynamic column and optional dropping ---
        df_clean, partial_dup_ids, true_dups_dropped = _check_duplicates(df_original, unique_col, drop_true_duplicates)

        # Use the cleaned DataFrame from here on. Reset index so it matches reconstructed batches.
        df_original = df_clean.reset_index(drop=True)
        
        if create_test_file:
            df_test = df_original.iloc[:10]
            test_filename = os.path.join(output_dir, f"{output_name}_Test.csv")
            df_test.to_csv(test_filename, index=False)
            generated_files.append(test_filename)
            df_splitting = df_original.iloc[10:]
        else:
            df_splitting = df_original
        
        total_rows = len(df_splitting)
        num_batches = (total_rows // rows_per_batch) + (1 if total_rows % rows_per_batch != 0 else 0)
        
        for i in range(num_batches):
            start_idx = i * rows_per_batch
            end_idx = start_idx + rows_per_batch
            batch_df = df_splitting.iloc[start_idx:end_idx]
            
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
            dup_report = _find_dup_locations(generated_files, partial_dup_ids, unique_col)
            parts.append(f"Duplicates found in input file for column '{unique_col}': {', '.join(str(x) for x in partial_dup_ids)}\n\n{dup_report}")

        # Validation (content-only, to ignore dtype inference differences across batches)
        df_total_reconstructed = pd.concat([pd.read_csv(f, low_memory=False) for f in generated_files], ignore_index=True)
        
        # Check if they are basically the same content by converting to string first
        # This ignores dtype mismatches (like int vs float) but catches data loss
        content_match = False
        if len(df_original) == len(df_total_reconstructed):
            content_match = df_original.astype(str).equals(df_total_reconstructed.astype(str))
            
        if content_match:
            test_line = f"Created {output_name}_Test.csv and " if create_test_file else ""
            # If we deduplicated, just show the report. If not, confirm validation.
            header = f"Split complete: {test_line}{num_batches} batches created."
            if true_dups_dropped == 0:
                header = f"Validation Passed!\n{header}"
            
            parts.insert(0, header)
            if completion_callback:
                completion_callback(True, "\n\n".join(parts))
        else:
            # This only happens if there's an internal processing error (data lost during split)
            err_type = "expected data"
            parts.insert(0, f"⚠️ WARNING: The generated batches do not match the {err_type}!")
            if completion_callback:
                completion_callback(False, "\n\n".join(parts))
            
    except Exception as e:
        if error_callback:
            error_callback(str(e))
