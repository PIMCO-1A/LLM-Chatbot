import sqlite3
import pandas as pd

# Path to your SQLite database
db_path = 'data/sec_nport_data_combined.db'

# SQL query: CHANGE THIS TO YOUR QUERY
sql_query = 'SELECT * FROM your_table;'  

# Connect to the db
conn = sqlite3.connect(db_path)

# Execute the SQL query, fetch the results into a df
df = pd.read_sql_query(sql_query, conn)

# close db connection
conn.close()

# Save the df to a csv file
df.to_csv('query_results.csv', index=False)

print("CSV file has been saved as 'query_results.csv'")
