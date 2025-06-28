import pandas as pd
import numpy as np
import json
import os

# Define a function to calculate LOESS (using a simple moving average for simplicity)
# This is a placeholder as true LOESS is complex and might require scipy or statsmodels
# For the purpose of this script, we'll prepare data for D3 to handle LOESS/LOWESS
def prepare_data_for_d3_loess(df, x_col, y_col):
    # D3 can compute LOESS. We just need to provide the x and y values.
    # This function is more of a conceptual placeholder if local calculation were needed.
    return df[[x_col, y_col]].copy()

def main():
    filepath = 'GoodReads_100k_books.csv'
    # Check if the uncompressed file exists, if not, try to find the compressed version
    if not os.path.exists(filepath):
        filepath_xz = filepath + '.xz'
        if os.path.exists(filepath_xz):
            print(f"Found compressed file: {filepath_xz}. Reading directly.")
            filepath = filepath_xz
        else:
            print(f"Error: Neither {filepath} nor {filepath_xz} found.")
            return

    try:
        # Read the CSV file (handles .xz transparently if pandas version is recent enough)
        # Use low_memory=False to avoid dtype inference issues with mixed types.
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Select and rename columns
    df = df[['pages', 'desc', 'reviews', 'rating']].copy()
    df.rename(columns={'pages': 'pages', 'desc': 'description', 'reviews': 'reviews', 'rating': 'rating'}, inplace=True)

    # Compute blurb length
    df['blurb'] = df['description'].astype(str).apply(len)

    # Convert columns to numeric, coercing errors to NaN
    numeric_cols = ['pages', 'reviews', 'rating', 'blurb']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with NaN in critical numeric columns after conversion
    df.dropna(subset=numeric_cols, inplace=True)

    # Ensure correct dtypes after potential coercion and dropna
    df['pages'] = df['pages'].astype(float) # Or int if appropriate after na check
    df['reviews'] = df['reviews'].astype(float)
    df['rating'] = df['rating'].astype(float)
    df['blurb'] = df['blurb'].astype(float)


    # Outlier clipping
    for col in ['pages', 'reviews', 'rating', 'blurb']:
        lower_percentile = df[col].quantile(0.005)
        upper_percentile = df[col].quantile(0.995)
        df = df[(df[col] >= lower_percentile) & (df[col] <= upper_percentile)]

    # Random sampling
    if len(df) > 5000:
        df = df.sample(n=5000, random_state=42)

    # Prepare final data for JSON
    output_data = df[['pages', 'blurb', 'reviews', 'rating']].to_dict(orient='records')

    # Dump to JSON
    output_json_path = 'scatter_data.json'
    with open(output_json_path, 'w') as f:
        json.dump(output_data, f)

    # Check JSON file size
    file_size = os.path.getsize(output_json_path)
    print(f"Final JSON file size: {file_size} bytes")

    if file_size > 2 * 1024 * 1024:
        print("Warning: JSON file size exceeds 2MB limit.")

if __name__ == '__main__':
    main()
