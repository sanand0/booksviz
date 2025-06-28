import pandas as pd
import numpy as np
import json
import os

def iqr_outlier_removal(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

def main():
    source_filepath = 'GoodReads_100k_books.csv'
    # Check if the uncompressed file exists, if not, try to find the compressed version
    if not os.path.exists(source_filepath):
        source_filepath_xz = source_filepath + '.xz'
        if os.path.exists(source_filepath_xz):
            print(f"Found compressed file: {source_filepath_xz}. Reading directly.")
            source_filepath = source_filepath_xz
        else:
            print(f"Error: Neither {source_filepath} nor {source_filepath_xz} found.")
            return

    try:
        # Specify dtypes for potentially problematic columns to avoid mixed type warnings
        # and ensure correct data loading. 'pages' can be large, 'reviewcount' and 'totalratings' too.
        # 'rating' is float. 'title', 'author' are strings.
        dtype_spec = {
            'title': str,
            'author': str,
            'rating': float, # Average rating
            'pages': float, # Number of pages - read as float for potential NaNs then convert to Int64
            'reviewcount': float, # Number of text reviews - read as float for NaNs then Int64
            'totalratings': float # Total star ratings - read as float for NaNs then Int64
        }
        # Let's first get the header to confirm column names
        try:
            header_df = pd.read_csv(source_filepath, nrows=0) # Read only header
            print(f"CSV Columns: {header_df.columns.tolist()}")
        except Exception as e:
            print(f"Error reading CSV header: {e}")
            return

        # Correct column names based on typical Kaggle dataset for Goodreads
        # Assuming 'reviews' in CSV is actually 'review_count' or similar, let's use what's common
        # The error said 'reviewcount' was not found. Let's find the actual name.
        # Common names: 'reviews', 'review_count', 'text_reviews_count'
        # Let's assume 'reviews' is the text review count based on previous usage.
        # The error was "Usecols do not match columns, columns expected but not found: ['reviewcount']"
        # This means 'reviewcount' as I typed it is not in the CSV.
        # The original CSV (from a quick search of similar datasets on Kaggle) often has 'reviews' for text review counts.
        # And 'ratings_count' for total ratings. My previous `totalratings` might be `ratings_count`.
        # Let's try with more robust column name finding or use the ones from my first successful script.
        # The first script used: df[['pages', 'desc', 'reviews', 'rating']]
        # 'reviews' was 'reviews column' -> this implies the CSV has a column named 'reviews'.
        # 'totalratings' was not used in the first script's output JSON, but the prompt now explicitly asks for it.

        # Confirmed from initial exploration of the CSV file (simulated):
        # The CSV has 'id', 'title', 'author', 'rating', 'pages', 'language', 'isbn',
        # 'genres', 'publisher', 'publishDate', 'desc', 'coverImg', 'link',
        # 'likedPercent', 'setting', 'series', 'bookformat', 'edition',
        # 'reviewcount', 'totalratings' -> These were the names I intended to use.
        # The error "Usecols do not match columns, columns expected but not found: ['reviewcount']"
        # suggests that my `dtype_spec` or `cols_to_read` for `reviewcount` was the issue, or the CSV is different than expected.

        # Let's re-verify the actual column names from the file if possible, or stick to what worked previously.
        # The error indicates 'reviewcount' is NOT a column.
        # The original problem description from the user for the first task said:
        #   reviews = reviews column
        #   rating = rating column
        # This suggests the CSV has 'reviews' and 'rating'.
        # Let's assume the CSV has 'reviews' (for text review count) and 'ratings_count' (for total ratings).
        # If 'totalratings' is not found, I'll need to adjust.

        # Corrected cols_to_read based on common CSV structures and the error.
        # The error "Usecols do not match columns, columns expected but not found: ['reviewcount']"
        # means `reviewcount` is not a column name.
        # Let's assume the column for number of text reviews is just 'reviews'.
        # And the column for total number of ratings is 'ratings_count' or 'totalRatings'.
        # The prompt for *this* task says:
        #   reviews: Number of reviews.
        #   totalratings: Total number of ratings the book has received.
        # This implies these are the target conceptual names, not necessarily the CSV headers.
        # I will use the CSV headers: 'reviews' for text review count, and 'totalRatings' for total ratings count.
        # If these are wrong, the script will fail again, and I'll need to inspect the actual CSV header.
        # The previous script used 'reviews' (from CSV) for review_count and 'rating' (from CSV) for rating.
        # It did not use a 'totalratings' field from the CSV.
        # The current CSV *does* have `reviewcount` and `totalratings` as per the `GoodReads_100k_books.csv.xz` structure.
        # The error was "Usecols do not match columns, columns expected but not found: ['reviewcount']"
        # This is very strange if the file indeed has it.
        # One possible issue: case sensitivity or hidden characters in column names.
        # Let's try reading all columns first and then select, to see what pandas reads as column names.

        df_full_header = pd.read_csv(source_filepath, nrows=1)
        actual_columns = df_full_header.columns.tolist()
        print(f"Actual columns found in CSV: {actual_columns}")

        # Define mapping from desired conceptual fields to actual CSV columns
        # This makes it easier to adapt if CSV column names vary slightly.
        # Based on the print output of actual_columns, I will confirm these.
        # For now, assuming the names are as expected from the problem description for the CSV itself.
        # The previous error implies 'reviewcount' was not found.
        # Let's assume the CSV columns are: 'title', 'author', 'rating', 'pages', 'reviews', 'totalRatings'
        # This is a common pattern. The error 'reviewcount' not found is the primary clue.

        # Based on a typical GoodReads dataset structure like "Goodreads_Books_1M.csv" or similar:
        # 'title', 'authors', 'average_rating', 'num_pages', 'text_reviews_count', 'ratings_count'
        # The provided file is "GoodReads_100k_books.csv".
        # The previous run's output showed:
        # CSV Columns: ['author', 'bookformat', 'desc', 'genre', 'img', 'isbn', 'isbn13', 'link', 'pages', 'rating', 'reviews', 'title', 'totalratings']
        # Actual columns found in CSV: ['author', 'bookformat', 'desc', 'genre', 'img', 'isbn', 'isbn13', 'link', 'pages', 'rating', 'reviews', 'title', 'totalratings']
        # Error reading CSV: Usecols do not match columns, columns expected but not found: ['reviewcount']

        # The actual column names are 'reviews' (for number of text reviews) and 'totalratings' (for total number of ratings).
        # The 'rating' column is the average rating. 'pages', 'title', 'author' are also present.

        actual_cols_from_log = ['author', 'bookformat', 'desc', 'genre', 'img', 'isbn', 'isbn13', 'link', 'pages', 'rating', 'reviews', 'title', 'totalratings']
        print(f"Confirmed CSV Columns (from log): {actual_cols_from_log}")

        cols_to_read = ['title', 'author', 'rating', 'pages', 'reviews', 'totalratings']

        # Ensure all cols_to_read are in actual_cols_from_log
        missing_cols = [col for col in cols_to_read if col not in actual_cols_from_log]
        if missing_cols:
            print(f"Critical error: Columns {missing_cols} are expected but not found in CSV headers {actual_cols_from_log}.")
            return

        # Original dtype_spec was:
        # dtype_spec = {
        #     'title': str, 'author': str, 'rating': float, 'pages': float,
        #     'reviewcount': float, 'totalratings': float # 'reviewcount' was the old problematic one
        # }
        # New dtype_spec based on actual column names:
        dtype_spec_updated = {
            'title': str,
            'author': str,
            'rating': float,      # This is the average rating
            'pages': float,       # Number of pages
            'reviews': float,     # This is the number of text reviews (formerly misidentified as 'reviewcount')
            'totalratings': float # This is the total number of ratings
        }

        df = pd.read_csv(source_filepath, usecols=cols_to_read, dtype=dtype_spec_updated, low_memory=False)
        print(f"Successfully read {len(df)} rows from {source_filepath} using corrected column list: {cols_to_read}")

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # No renaming needed for 'reviews' or 'totalratings' as CSV names match desired output names.
    # 'rating' from CSV is average rating, which is also the desired name for Plot2 Y-axis.
    # So, no major renames like 'rating' to 'average_rating' and back are needed if direct names are used.
    # Let's keep internal variable `average_rating` for clarity if it represents the concept,
    # but ensure JSON output matches plot spec ('rating' for average_rating).

    # df.rename(columns={'rating': 'average_rating'}, inplace=True) # Optional: internal clarity
    # Let's use 'rating' directly as it's less confusing.

    numeric_cols_for_processing = ['pages', 'reviews', 'totalratings', 'rating']

    for col in numeric_cols_for_processing:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=['title', 'author'] + numeric_cols_for_processing, inplace=True)
    print(f"Rows after dropping NaNs in critical columns: {len(df)}")

    # Convert float columns that should be integers to Int64 if it makes sense.
    # For plotting, float is generally fine.
    # 'pages', 'reviews', 'totalratings' are counts, so int is semantically better.
    for col in ['pages', 'reviews', 'totalratings']:
         # Before converting to int, ensure no new NaNs were introduced by pd.to_numeric if a column was all bad strings
        if df[col].isnull().any():
            print(f"Warning: Column '{col}' contains NaNs before attempting int conversion. Dropping these rows.")
            df.dropna(subset=[col], inplace=True)
        df[col] = df[col].astype(np.int64)

    # Apply IQR outlier removal
    initial_rows = len(df)
    # The problem refers to 'rating' for average rating, 'reviews' for review count.
    for col in ['reviews', 'totalratings', 'pages', 'rating']: # Use final column names
        df = iqr_outlier_removal(df, col)
        print(f"Rows after IQR on '{col}': {len(df)}")

    if len(df) == 0:
        print("Error: All data removed by IQR filtering. Check data distribution or IQR parameters.")
        return

    print(f"Total rows removed by IQR: {initial_rows - len(df)}")

    max_rows = 10000
    if len(df) > max_rows:
        print(f"Dataset has {len(df)} rows after filtering, sampling down to {max_rows}.")
        df = df.sample(n=max_rows, random_state=42)

    # Prepare final data for JSON. Names should be:
    # title, author, pages, reviews, totalratings, rating (for average_rating)
    # All these names are already columns in df.

    # Create page_group bins
    # First, let's see the distribution of 'pages' after IQR to define sensible bins
    print("Page column statistics after IQR and before sampling (if any):")
    print(df['pages'].describe(percentiles=[.1, .25, .5, .75, .9, .95, .99]))

    # Define bins and labels based on typical book lengths and the distribution
    # These bins are chosen to give a reasonable number of categories for the box plot.
    # Max pages after IQR was around 700-800 in previous runs, but let's make bins flexible.
    # The IQR for pages was: 73922 rows left. Let's assume a typical max around 800-1000 pages post-IQR.
    page_bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, np.inf]
    page_labels = ['0-100', '101-200', '201-300', '301-400', '401-500', '501-600', '601-700', '701-800', '800+']

    # If the max pages is much lower, these bins might be too granular at the top end or create empty groups.
    # Let's make the bins dynamic based on max_pages after IQR, or use fixed sensible ones.
    # Given IQR removed outliers, max pages should be somewhat reasonable.
    # The previous run showed page IQR left values up to a certain point.
    # Max from describe() will inform this. For now, fixed bins are okay.

    df['page_group'] = pd.cut(df['pages'], bins=page_bins, labels=page_labels, right=True, include_lowest=True)
    print("\nPage group distribution:")
    print(df['page_group'].value_counts().sort_index())

    # Ensure 'page_group' is included in the output
    output_df = df[['title', 'author', 'pages', 'reviews', 'totalratings', 'rating', 'page_group']].copy()

    output_data = output_df.to_dict(orient='records')

    output_json_path = 'goodreads_plotly_data.json'
    with open(output_json_path, 'w') as f:
        json.dump(output_data, f)

    file_size = os.path.getsize(output_json_path)
    print(f"Final JSON file '{output_json_path}' size: {file_size / 1024:.2f} KB")
    print(f"Number of records in JSON: {len(output_data)}")

    if file_size > 2 * 1024 * 1024:
        print(f"Warning: JSON file size ({file_size} bytes) exceeds 2MB limit.")

if __name__ == '__main__':
    main()
