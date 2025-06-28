import pandas as pd
import numpy as np
import json
import os

# Define file paths
input_csv_xz = 'GoodReads_100k_books.csv.xz'
output_json = 'scatter_data.json'

# Columns to read from CSV and their desired final names
cols_to_use = {'pages': 'pages', 'desc': 'desc', 'reviews': 'reviews', 'rating': 'rating'}

# Determine actual columns present in the CSV to avoid errors if some are missing
try:
    df_header_check = pd.read_csv(input_csv_xz, compression='xz', encoding='utf-8', nrows=0) # Read only header
except UnicodeDecodeError:
    df_header_check = pd.read_csv(input_csv_xz, compression='xz', encoding='latin1', nrows=0) # Read only header

actual_cols_in_csv = df_header_check.columns.tolist()
cols_to_actually_read = [col for col in cols_to_use.keys() if col in actual_cols_in_csv]
final_renames = {k: v for k, v in cols_to_use.items() if k in cols_to_actually_read}

if len(cols_to_actually_read) != len(cols_to_use.keys()):
    missing_cols = set(cols_to_use.keys()) - set(cols_to_actually_read)
    print(f"Info: The following specified columns were not found in the CSV and will be ignored: {missing_cols}")

# Read the CSV file, handling potential decoding errors
try:
    df = pd.read_csv(input_csv_xz, usecols=cols_to_actually_read, compression='xz', encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(input_csv_xz, usecols=cols_to_actually_read, compression='xz', encoding='latin1')

# Rename columns
df = df.rename(columns=final_renames)

# Compute blurb length
# Ensure 'desc' column exists before processing
if 'desc' in df.columns:
    df['blurb'] = df['desc'].astype(str).str.len()
    df = df.drop(columns=['desc']) # Drop original description column
else:
    print("Warning: 'desc' column not found. 'blurb' feature cannot be created.")
    df['blurb'] = 0 # Create a dummy blurb column if desc is missing

# Identify numeric columns for outlier clipping
numeric_cols = ['pages', 'reviews', 'rating', 'blurb']

# Convert columns to numeric, coercing errors to NaN
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with NaN values that might have been introduced by coercion or were already present
df = df.dropna(subset=numeric_cols)

# Outlier clipping function
def clip_outliers(df_series):
    lower_percentile = 0.5
    upper_percentile = 99.5
    lower_bound = df_series.quantile(lower_percentile / 100.0)
    upper_bound = df_series.quantile(upper_percentile / 100.0)
    return df_series.clip(lower=lower_bound, upper=upper_bound)

# Apply outlier clipping to specified numeric columns
for col in ['pages', 'reviews', 'rating']: # 'blurb' is not clipped as per instructions
    if col in df.columns: # Check if column exists after potential drops
        df[col] = clip_outliers(df[col])

# Drop rows that became NaN after clipping (if any, though clip shouldn't introduce NaNs)
df = df.dropna(subset=numeric_cols)


# Randomly sample max 5000 rows
if len(df) > 5000:
    df = df.sample(n=5000, random_state=42)

# Prepare data for JSON output
output_data = df[['pages', 'blurb', 'reviews', 'rating']].to_dict(orient='records')

# Dump to JSON
with open(output_json, 'w') as f:
    json.dump(output_data, f)

# Check JSON file size
file_size_bytes = os.path.getsize(output_json)
file_size_mb = file_size_bytes / (1024 * 1024)

print(f"Data processing complete. Output saved to {output_json}")
print(f"Final JSON file size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")

if file_size_mb > 2:
    print("Warning: JSON file size exceeds 2 MB limit.")

# Clean up by removing the large CSV if it was uncompressed
# This is not strictly necessary here as we read from xz directly,
# but good practice if an intermediate uncompressed file was created.
# if os.path.exists('GoodReads_100k_books.csv'):
#     os.remove('GoodReads_100k_books.csv')
