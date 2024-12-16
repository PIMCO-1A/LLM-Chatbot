import os
import pandas as pd

data_folder_path = "/Users/mayzheng/Library/CloudStorage/GoogleDrive-mayzheng@g.ucla.edu/.shortcut-targets-by-id/1l6Ivj88DSwtaBno_3NISgPRWZGGHxlo9/Team PIMCO 1A/nport data"

def extract_year_and_quarter(folder_name):
    """
    Extracts year and quarter from the folder name and converts them to integers.
    Example: "2024q2_nport" -> year: 2024, quarter: 2
    """
    year = int(folder_name[:4])
    quarter = int(folder_name[5])
    return year, quarter

def load_and_process_data():
    """
    Generator that loads and processes data files from the specified data folder.
    Steps:
    1. Read all folders/files.
    2. Randomly sample 1000 rows from each table (if available).
    3. Add year/quarter columns.
    4. Combine tables of the same type across all folders.
    """
    combined_data = {}

    print("Starting to load and process data...")

    for root, dirs, files in os.walk(data_folder_path):
        folder_name = os.path.basename(root)
        try:
            year, quarter = extract_year_and_quarter(folder_name)
        except ValueError:
            continue

        for file in files:
            if file.endswith(".tsv"):
                tsv_file_path = os.path.join(root, file)
                print(f"Processing file: {tsv_file_path}")

                try:
                    df = pd.read_csv(tsv_file_path, sep='\t', low_memory=False, on_bad_lines='skip')
                    df = df.sample(n=min(1000, len(df)), random_state=42)  # Randomly sample 1000 rows
                    df['YEAR'] = year
                    df['QUARTER'] = quarter

                    table_name = os.path.splitext(file)[0]
                    if table_name not in combined_data:
                        combined_data[table_name] = []
                    combined_data[table_name].append(df)
                except Exception as e:
                    print(f"Error reading file {file}: {e}")
                    continue

    # Combine dataframes for each table type
    for table_name, dfs in combined_data.items():
        combined_df = pd.concat(dfs, ignore_index=True)
        yield combined_df, table_name
