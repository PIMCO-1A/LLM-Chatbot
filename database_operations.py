from sqlalchemy import create_engine, inspect
import pandas as pd

# Create a connection to the SQLite database
def create_engine_connection(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    return engine

# Save the sampled data to the database
def save_to_database(engine, df_sampled, table_name):
    try:
        # Trim fields with >85% missing values
        df_sampled = trim_fields(df_sampled)
        
        # Save to database
        df_sampled.to_sql(table_name, engine, if_exists='append', index=False)
        print(f"Data saved to {table_name} in the database.")
    except Exception as e:
        print(f"Error saving data: {e}")

# Function to trim fields with >85% missing values
def trim_fields(df):
    missing_percent = df.isnull().mean() * 100
    columns_to_drop = missing_percent[missing_percent > 85].index.tolist()
    
    if columns_to_drop:
        print(f"Dropping columns with >85% missing values: {columns_to_drop}")
        df = df.drop(columns=columns_to_drop)
    
    return df
