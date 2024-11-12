from pathlib import Path
from data_loading import load_and_sample_data
from database_operations import create_engine_connection, save_to_database

# Define the database path
db_path = Path("data/sec_nport_data.db")

# Create the database directory if it doesn't exist
db_path.parent.mkdir(exist_ok=True)

# Connect to the database
print("Connecting to the database...")
engine = create_engine_connection(str(db_path))
print("Connected to the database.")

# Process and save each file
for df_sampled, table_name in load_and_sample_data():
    print(f"Saving data to table '{table_name}'...")
    save_to_database(engine, df_sampled, table_name)
    print(f"Data saved for table '{table_name}'.")
