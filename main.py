from pathlib import Path
import pandas as pd
from data_loading import load_and_process_data
from database_operations import create_engine_connection, save_to_database, drop_high_missing_columns

# Define the paths
db_path = Path("data/sec_nport_data_combined.db")

# Create the database directory if it doesn't exist
db_path.parent.mkdir(exist_ok=True)

# Connect to the database
print("Connecting to the database...")
engine = create_engine_connection(str(db_path))
print("Connected to the database.")

# Process, combine, and save each table to the database
print("Processing and saving files...")
combined_tables = {}

for df, table_name in load_and_process_data():
    df = drop_high_missing_columns(df, threshold=85)
    print(f"Dropped fields with >85% missing values for table '{table_name}'.")

    if table_name not in combined_tables:
        combined_tables[table_name] = []
    combined_tables[table_name].append(df)

# Combine tables across all quarters and save to the database
for table_name, dfs in combined_tables.items():
    combined_df = pd.concat(dfs, ignore_index=True)
    save_to_database(engine, combined_df, table_name)
    print(f"Data saved for combined table '{table_name}'.")
