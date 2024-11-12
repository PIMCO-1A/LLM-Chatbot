from pathlib import Path
import pandas as pd  # Import pandas for data manipulation
from data_loading import load_and_process_data
from database_operations import create_engine_connection, save_to_database

# Define the database path
db_path = Path("data/sec_nport_data_subset.db")
data_folder_path = "/Users/mayzheng/Library/CloudStorage/GoogleDrive-mayzheng@g.ucla.edu/.shortcut-targets-by-id/1l6Ivj88DSwtaBno_3NISgPRWZGGHxlo9/Team PIMCO 1A/nport data"

# Create the database directory if it doesn't exist
db_path.parent.mkdir(exist_ok=True)

# Connect to the database
print("Connecting to the database...")
engine = create_engine_connection(str(db_path))
print("Connected to the database.")

# Load all CUSIPs from the data
print("Loading and processing data...")
cusips = set()
for df, _ in load_and_process_data():
    cusips.update(df['CUSIP'].drop_duplicates().tolist())  # Collect unique CUSIPs from the data

# Sample 1,000 unique CUSIPs
print("Sampling 1,000 unique CUSIPs...")
sampled_cusips = pd.Series(list(cusips)).sample(n=1000, random_state=42)

# Process and save each file to the database
print("Processing and saving files...")
for df_sampled, table_name in load_and_process_data():
    # Filter rows by sampled CUSIPs
    df_sampled = df_sampled[df_sampled['CUSIP'].isin(sampled_cusips)]
    
    print(f"Saving data to table '{table_name}'...")
    save_to_database(engine, df_sampled, table_name)
    print(f"Data saved for table '{table_name}'.")
