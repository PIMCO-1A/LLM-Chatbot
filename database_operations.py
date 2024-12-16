from sqlalchemy import create_engine
import pandas as pd

def create_engine_connection(db_path):
    """
    Creates a connection to the SQLite database.
    """
    engine = create_engine(f'sqlite:///{db_path}')
    return engine

def save_to_database(engine, data, table_name):
    """
    Saves processed data to the database.
    """
    try:
        data.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Data saved to {table_name} in the database.")
    except Exception as e:
        print(f"Error saving data to table '{table_name}': {e}")

def drop_high_missing_columns(data, threshold=85):
    """
    Drops columns with more than a given percentage of missing values,
    ensuring that columns containing 'CUSIP' are never dropped.
    """
    missing_percent = data.isnull().mean() * 100
    columns_to_drop = [
        col for col in missing_percent[missing_percent > threshold].index
        if 'CUSIP' not in col.upper()
    ]
    return data.drop(columns=columns_to_drop)
