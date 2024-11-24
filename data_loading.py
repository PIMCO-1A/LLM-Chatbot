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

def standardize_cusip_columns(df):
    """
    Standardizes all columns containing the keyword 'CUSIP' to be titled 'CUSIP'.
    """
    for col in df.columns:
        if 'CUSIP' in col.upper():
            df.rename(columns={col: 'CUSIP'}, inplace=True)
    return df

def load_and_process_data():
    """
    Generator that loads and processes data files from the specified data folder.
    Steps:
    1. Read all folders/files.
    2. Extract 1000 unique CUSIPs from FUND_REPORTED_HOLDING.tsv.
    3. Use primary keys to filter rows from other tables.
    4. Add year/quarter columns and propagate CUSIP values.
    5. Combine tables of the same type across all folders.
    """
    combined_data = {}
    sampled_cusips = set()
    primary_keys = {}

    print("Starting to load and process data...")

    # Process FUND_REPORTED_HOLDING.tsv first (only once)
    for root, dirs, files in os.walk(data_folder_path):
        folder_name = os.path.basename(root)
        try:
            year, quarter = extract_year_and_quarter(folder_name)
        except ValueError:
            continue

        fund_file_path = os.path.join(root, "FUND_REPORTED_HOLDING.tsv")
        if os.path.exists(fund_file_path):
            print(f"Processing FUND_REPORTED_HOLDING.tsv once: {fund_file_path}")
            try:
                fund_df = pd.read_csv(fund_file_path, sep='\t', low_memory=False, on_bad_lines='skip')
                fund_df = standardize_cusip_columns(fund_df)
                fund_df = fund_df.dropna(subset=['CUSIP'])

                if 'ACCESSION_NUMBER' in fund_df.columns and 'HOLDING_ID' in fund_df.columns:
                    # Extract random CUSIPs and primary keys
                    sampled_cusips.update(fund_df['CUSIP'].drop_duplicates().sample(n=1000, random_state=42))
                    primary_keys.update(
                        fund_df[fund_df['CUSIP'].isin(sampled_cusips)][['ACCESSION_NUMBER', 'HOLDING_ID']]
                        .set_index('ACCESSION_NUMBER')['HOLDING_ID'].to_dict()
                    )

                    # Filter fund_df to keep only rows with sampled CUSIPs
                    fund_df = fund_df[fund_df['CUSIP'].isin(sampled_cusips)]
                    fund_df['YEAR'] = year
                    fund_df['QUARTER'] = quarter

                    # Yield FUND_REPORTED_HOLDING data immediately for saving
                    yield fund_df, "FUND_REPORTED_HOLDING"
            except Exception as e:
                print(f"Error processing FUND_REPORTED_HOLDING.tsv: {e}")
            break  # Exit after processing FUND_REPORTED_HOLDING.tsv once

    # Process other files in all folders
    for root, dirs, files in os.walk(data_folder_path):
        folder_name = os.path.basename(root)
        try:
            year, quarter = extract_year_and_quarter(folder_name)
        except ValueError:
            continue

        for file in files:
            if file.endswith(".tsv") and file != "FUND_REPORTED_HOLDING.tsv":
                tsv_file_path = os.path.join(root, file)
                print(f"Processing file: {tsv_file_path}")

                try:
                    df = pd.read_csv(tsv_file_path, sep='\t', low_memory=False, on_bad_lines='skip')
                    table_name = os.path.splitext(file)[0]

                    # Apply filtering using primary keys
                    if 'ACCESSION_NUMBER' in df.columns:
                        df = df[df['ACCESSION_NUMBER'].isin(primary_keys.keys())]
                    if 'HOLDING_ID' in df.columns:
                        df = df[df['HOLDING_ID'].isin(primary_keys.values())]

                    df['YEAR'] = year
                    df['QUARTER'] = quarter

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
