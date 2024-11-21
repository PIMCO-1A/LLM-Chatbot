import os
import pandas as pd

data_folder_path = "/Users/mayzheng/Library/CloudStorage/GoogleDrive-mayzheng@g.ucla.edu/.shortcut-targets-by-id/1l6Ivj88DSwtaBno_3NISgPRWZGGHxlo9/Team PIMCO 1A/nport data"
schema_file_path = "Table_Schema.txt"

def load_schema(schema_file):
    """
    Parse the schema file to extract table and column details.
    """
    schema = {}
    current_table = None
    
    with open(schema_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Table:"):
                current_table = line.split(':')[1].strip().split()[0]
                schema[current_table] = []
            elif line.startswith('-') and current_table:
                column = line.split('(')[0].replace('-', '').strip()
                schema[current_table].append(column)
    
    return schema

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

def propagate_cusip_values(df):
    """
    Fills missing CUSIP values within groups defined by ISSUER_NAME and ISSUE_TITLE.
    """
    if 'CUSIP' in df.columns and 'ISSUER_NAME' in df.columns and 'ISSUE_TITLE' in df.columns:
        df['CUSIP'] = df.groupby(['ISSUER_NAME', 'ISSUE_TITLE'])['CUSIP'].ffill().bfill()
    return df

def load_and_process_data():
    """
    Generator that loads and processes data files from the specified data folder.
    Steps:
    1. Read all folders/files.
    2. Standardize CUSIP column names.
    3. Drop files without a 'CUSIP' column.
    4. Propagate missing CUSIP values and drop rows with missing CUSIPs.
    5. Extract year/quarter, convert to integers, and add as columns.
    6. Drop fields with 85%+ missing values (except CUSIP, YEAR, and QUARTER).
    """
    schema = load_schema(schema_file_path)
    print("Loaded schema:", schema)
    
    combined_data = {}
    
    print("Starting to load and process data...")
    for root, dirs, files in os.walk(data_folder_path):
        folder_name = os.path.basename(root)
        try:
            year, quarter = extract_year_and_quarter(folder_name)
        except ValueError:
            continue  # Skip invalid folder names
        
        for file in files:
            if file.endswith(".tsv"):
                tsv_file_path = os.path.join(root, file)
                print(f"Processing file: {tsv_file_path}")
                
                try:
                    df = pd.read_csv(tsv_file_path, sep='\t', low_memory=False, on_bad_lines='skip')
                except Exception as e:
                    print(f"Error reading file {file}: {e}")
                    continue
                
                table_name = os.path.splitext(file)[0]
                if table_name not in schema:
                    print(f"Skipping table not found in schema: {table_name}")
                    continue
                
                valid_columns = schema[table_name]
                df = df[[col for col in df.columns if col in valid_columns]]
                
                df = standardize_cusip_columns(df)
                if 'CUSIP' not in df.columns:
                    print(f"Skipping table '{table_name}' as it does not have a CUSIP column.")
                    continue
                
                df['YEAR'] = year
                df['QUARTER'] = quarter
                
                df = propagate_cusip_values(df)
                df = df.dropna(subset=['CUSIP'])
                
                missing_percent = df.isnull().mean() * 100
                columns_to_drop = missing_percent[missing_percent > 85].index.tolist()
                columns_to_drop = [col for col in columns_to_drop if col not in ['CUSIP', 'YEAR', 'QUARTER']]
                df = df.drop(columns=columns_to_drop)
                
                # Combine data across all folders for the same table
                if table_name not in combined_data:
                    combined_data[table_name] = []
                combined_data[table_name].append(df)
    
    # Combine dataframes for each table
    for table_name, dfs in combined_data.items():
        combined_df = pd.concat(dfs, ignore_index=True)
        yield combined_df, table_name










