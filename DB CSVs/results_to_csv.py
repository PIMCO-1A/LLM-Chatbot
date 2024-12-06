import sqlite3
import pandas as pd

# Path to your SQLite database
db_path = '../data/sec_nport_data_large.db'

# SQL query: CHANGE THIS TO YOUR QUERY
sql_query = """
SELECT fri.SERIES_NAME
FROM FUND_REPORTED_INFO fri
WHERE EXISTS (
    SELECT 1
    FROM FWD_FOREIGNCUR_CONTRACT_SWAP fcs
    JOIN FUND_REPORTED_HOLDING frh ON fcs.HOLDING_ID = frh.HOLDING_ID
    WHERE fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
    AND fcs.DESC_CURRENCY_SOLD = 'USD'
    AND fcs.YEAR = 2020
)
AND fri.YEAR = 2020;
"""

# Connect to the db
conn = sqlite3.connect(db_path)

# Execute the SQL query, fetch the results into a df
df = pd.read_sql_query(sql_query, conn)

# close db connection
conn.close()

# Save the df to a csv file
df.to_csv('Hard14.csv', index=False)

print("CSV file has been saved.")
