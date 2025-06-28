import pandas as pd
import numpy as np
import json
import os
import lzma

def preprocess_data(input_filepath='GoodReads_100k_books.csv.xz', output_filepath='scatter_data.json'):
    """
    Reads, preprocesses, and samples book data, then saves it to a JSON file.
    """
    try:
        # Try reading directly with pandas, assuming it can use the built-in lzma
        df = pd.read_csv(input_filepath, compression='xz', on_bad_lines='skip')
    except Exception as e:
        print(f"Pandas could not read xz directly ({e}), attempting manual decompression...")
        # Fallback to manual decompression if pandas fails
        try:
            with lzma.open(input_filepath, 'rt', encoding='utf-8') as f:
                df = pd.read_csv(f, on_bad_lines='skip')
        except Exception as manual_e:
            print(f"Manual decompression also failed: {manual_e}")
            raise Exception("Could not read the compressed CSV file.") from manual_e

    # Select the required columns using their actual names in the CSV
    # Actual names: 'pages', 'desc', 'reviews', 'rating'
    df = df[['pages', 'desc', 'reviews', 'rating']]

    # Compute blurb length from 'desc'
    df['blurb'] = df['desc'].astype(str).apply(len)
    df.drop(columns=['desc'], inplace=True) # Drop original description column

    # Columns for processing and final output are: 'pages', 'blurb', 'reviews', 'rating'
    numeric_cols = ['pages', 'blurb', 'reviews', 'rating']

    # Convert columns to numeric, coercing errors
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with NaN values that might have resulted from coercion or were already present
    df.dropna(subset=numeric_cols, inplace=True)

    # Outlier clipping: keep rows inside the 0.5 - 99.5 percentile range for each numeric column
    for col in numeric_cols:
        lower_percentile = df[col].quantile(0.005)
        upper_percentile = df[col].quantile(0.995)
        # Ensure lower is not greater than upper, can happen with skewed data or small unique values
        if lower_percentile > upper_percentile:
            print(f"Warning: Lower percentile ({lower_percentile}) > upper percentile ({upper_percentile}) for column {col}. Skipping clipping for this column or adjusting logic might be needed.")
            # Depending on desired behavior, one might skip clipping for this column,
            # or use min/max of the column if percentiles are inverted.
            # For now, we proceed, which might result in an empty DataFrame for this column's filter if not handled.
            # A robust way is to ensure df[col] >= lower_percentile and df[col] <= upper_percentile
            # only if lower_percentile <= upper_percentile.
            # However, pandas quantile behavior should generally prevent this unless data is very unusual.
        df = df[(df[col] >= lower_percentile) & (df[col] <= upper_percentile)]

    # Random sampling: max 5000 rows (seed = 42)
    if len(df) > 5000:
        df = df.sample(n=5000, random_state=42)
    elif len(df) == 0:
        print("Warning: DataFrame is empty after outlier clipping. The JSON output will be empty.")


    # Prepare data for JSON output with keys {pages, blurb, reviews, rating}
    # Ensure correct column order for the output list of dicts, though not strictly necessary
    # for `to_dict(orient='records')` as it uses column names as keys.
    output_data = df[['pages', 'blurb', 'reviews', 'rating']].to_dict(orient='records')

    # Dump to JSON
    with open(output_filepath, 'w') as f:
        json.dump(output_data, f)

    # Check file size
    file_size_bytes = os.path.getsize(output_filepath)
    file_size_mb = file_size_bytes / (1024 * 1024)

    print(f"Output file: {output_filepath}")
    print(f"Final JSON file size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")

    if file_size_mb > 2:
        print("Warning: JSON file size exceeds 2 MB.")
    else:
        print("JSON file size is within the 2 MB limit.")

if __name__ == '__main__':
    preprocess_data()
