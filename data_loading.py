import os
import pandas as pd

# Set the path to your data folder
data_folder_path = "/Users/mayzheng/Library/CloudStorage/GoogleDrive-mayzheng@g.ucla.edu/.shortcut-targets-by-id/1l6Ivj88DSwtaBno_3NISgPRWZGGHxlo9/Team PIMCO 1A/nport data"
n_samples = 10000  # Number of random samples to extract

def extract_year_and_quarter(folder_name):
    year = folder_name[:4]           # Extracts the first four characters as year, e.g., "2024"
    quarter = folder_name[4:6]       # Extracts "q2" from "2024q2_nport"
    return year, quarter

def load_and_sample_data():
    print("Starting to load and sample data...")
    for root, dirs, files in os.walk(data_folder_path):
        folder_name = os.path.basename(root)
        year, quarter = extract_year_and_quarter(folder_name)
        
        for file in files:
            if file.endswith(".tsv"):
                tsv_file_path = os.path.join(root, file)
                print(f"Processing file: {tsv_file_path}")
                
                # Load data, skipping bad lines
                df = pd.read_csv(tsv_file_path, sep='\t', low_memory=False, on_bad_lines='skip')
                
                # Add new columns for year and quarter
                df['year'] = year
                df['quarter'] = quarter
                
                # Sample the data if it exceeds n_samples
                if len(df) > n_samples:
                    df_sampled = df.sample(n=n_samples, random_state=42)
                else:
                    df_sampled = df
                
                yield df_sampled, os.path.splitext(file)[0]  # Yield sampled data and table name
