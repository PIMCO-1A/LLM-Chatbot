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

def sample_cusips(data, sample_size):
    """
    Randomly samples unique CUSIPs from the data.
    If the number of unique CUSIPs is less than the sample size, sample all available CUSIPs.
    """
    unique_cusips = data['CUSIP'].drop_duplicates()
    actual_sample_size = min(len(unique_cusips), sample_size)  # Adjust the sample size if necessary
    return unique_cusips.sample(n=actual_sample_size, random_state=42)

def filter_by_cusips(data, sampled_cusips):
    """
    Filters the data to include only rows with sampled CUSIPs.
    """
    return data[data['CUSIP'].isin(sampled_cusips)]










# from sqlalchemy import create_engine
# import pandas as pd

# def create_engine_connection(db_path):
#     """
#     Creates a connection to the SQLite database.
#     """
#     engine = create_engine(f'sqlite:///{db_path}')
#     return engine

# def save_to_database(engine, data, table_name):
#     """
#     Saves processed data to the database.
#     """
#     try:
#         data.to_sql(table_name, engine, if_exists='replace', index=False)
#         print(f"Data saved to {table_name} in the database.")
#     except Exception as e:
#         print(f"Error saving data to table '{table_name}': {e}")

# def sample_cusips(data, sample_size):
#     """
#     Randomly samples unique CUSIPs from the data.
#     If the number of unique CUSIPs is less than the sample size, sample all available CUSIPs.
#     """
#     unique_cusips = data['CUSIP'].drop_duplicates()
#     actual_sample_size = min(len(unique_cusips), sample_size)  # Adjust the sample size if necessary
#     return unique_cusips.sample(n=actual_sample_size, random_state=42)

# def filter_by_cusips(data, sampled_cusips):
#     """
#     Filters the data to include only rows with sampled CUSIPs.
#     """
#     return data[data['CUSIP'].isin(sampled_cusips)]





# from sqlalchemy import create_engine
# import pandas as pd

# # Create a connection to the SQLite database
# def create_engine_connection(db_path):
#     """
#     Creates a connection to the SQLite database.
#     """
#     engine = create_engine(f'sqlite:///{db_path}')
#     return engine

# # Save the processed data to the database
# def save_to_database(engine, data, table_name, schema):
#     """
#     Saves processed data to the database, ensuring it aligns with the schema.
#     Trims fields with >85% missing values before saving.
#     """
#     try:
#         # Validate columns against the schema
#         valid_columns = schema.get(table_name, [])
#         data = data[[col for col in data.columns if col in valid_columns]]
        
#         # Trim fields with >85% missing values
#         data = trim_fields(data)
        
#         # Save to database
#         data.to_sql(table_name, engine, if_exists='replace', index=False)
#         print(f"Data saved to {table_name} in the database.")
#     except Exception as e:
#         print(f"Error saving data to table '{table_name}': {e}")

# # Function to trim fields with >85% missing values
# def trim_fields(data):
#     """
#     Drops columns with more than 85% missing values.
#     """
#     missing_percent = data.isnull().mean() * 100
#     columns_to_drop = missing_percent[missing_percent > 85].index.tolist()
    
#     if columns_to_drop:
#         print(f"Dropping columns with >85% missing values: {columns_to_drop}")
#         data = data.drop(columns=columns_to_drop)
    
#     return data

# def sample_cusips(data, sample_size):
#     """
#     Randomly samples unique CUSIPs from the data.
#     """
#     sampled_cusips = data['CUSIP'].drop_duplicates().sample(n=sample_size, random_state=42)
#     return sampled_cusips

# def filter_by_cusips(data, sampled_cusips):
#     """
#     Filters the data to include only rows with sampled CUSIPs.
#     """
#     return data[data['CUSIP'].isin(sampled_cusips)]







