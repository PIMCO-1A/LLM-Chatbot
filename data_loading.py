import os
import pandas as pd

# Set the path to your data folder
data_folder_path = "/Users/mayzheng/Library/CloudStorage/GoogleDrive-mayzheng@g.ucla.edu/.shortcut-targets-by-id/1l6Ivj88DSwtaBno_3NISgPRWZGGHxlo9/Team PIMCO 1A/nport data"

def extract_year_and_quarter(folder_name):
    """
    Extracts year and quarter from the folder name.
    Example: "2024q2_nport" -> year: "2024", quarter: "q2"
    """
    year = folder_name[:4]           # Extracts the first four characters as year
    quarter = folder_name[4:6]       # Extracts the fifth and sixth characters (e.g., "q2")
    return year, quarter

def propagate_cusip_values(df):
    """
    Fills missing CUSIP values within groups defined by ISSUER_NAME and ISSUE_TITLE.
    Forward and backward fills are used to propagate values.
    """
    if 'CUSIP' in df.columns and 'ISSUER_NAME' in df.columns and 'ISSUE_TITLE' in df.columns:
        df['CUSIP'] = df.groupby(['ISSUER_NAME', 'ISSUE_TITLE'])['CUSIP'].ffill().bfill()
    return df

def load_and_process_data():
    """
    Generator that loads and processes data files from the specified data folder.
    Includes:
    - Extracting year and quarter
    - Propagating missing CUSIP values
    - Filtering rows with valid CUSIPs
    - Dropping rows with completely missing CUSIPs
    """
    print("Starting to load and process data...")
    for root, dirs, files in os.walk(data_folder_path):
        folder_name = os.path.basename(root)
        year, quarter = extract_year_and_quarter(folder_name)
        
        for file in files:
            if file.endswith(".tsv"):
                tsv_file_path = os.path.join(root, file)
                print(f"Processing file: {tsv_file_path}")
                
                # Load data, skipping bad lines
                try:
                    df = pd.read_csv(tsv_file_path, sep='\t', low_memory=False, on_bad_lines='skip')
                except Exception as e:
                    print(f"Error reading file {file}: {e}")
                    continue
                
                # Check if the table has a CUSIP column
                if 'CUSIP' not in df.columns:
                    print(f"Skipping table without CUSIP column: {file}")
                    continue
                
                # Add new columns for year and quarter
                df['year'] = year
                df['quarter'] = quarter
                
                # Propagate CUSIP values
                df = propagate_cusip_values(df)
                
                # Drop rows with missing CUSIP values
                df = df.dropna(subset=['CUSIP'])
                
                yield df, os.path.splitext(file)[0]  # Yield processed data and table name
