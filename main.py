from pathlib import Path
import pandas as pd
from data_loading import load_and_process_data
from database_operations import create_engine_connection, save_to_database, sample_cusips

# Define the paths
db_path = Path("data/sec_nport_data_subset.db")
data_folder_path = "/Users/mayzheng/Library/CloudStorage/GoogleDrive-mayzheng@g.ucla.edu/.shortcut-targets-by-id/1l6Ivj88DSwtaBno_3NISgPRWZGGHxlo9/Team PIMCO 1A/nport data"

# Create the database directory if it doesn't exist
db_path.parent.mkdir(exist_ok=True)

# Connect to the database
print("Connecting to the database...")
engine = create_engine_connection(str(db_path))
print("Connected to the database.")

# Process and save each file to the database
print("Processing and saving files...")
for df, table_name in load_and_process_data():
    print(f"Sampling 1,000 unique CUSIPs from table '{table_name}'...")
    sampled_cusips = sample_cusips(df, sample_size=1000)
    filtered_df = df[df['CUSIP'].isin(sampled_cusips)]
    save_to_database(engine, filtered_df, table_name)
    print(f"Data saved for table '{table_name}'.")















