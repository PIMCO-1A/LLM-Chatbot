import sqlite3
import pandas as pd

# Path to your SQLite database
db_path = '../data/sec_nport_data_large.db'

# SQL query: CHANGE THIS TO YOUR QUERY
sql_query = """
SELECT fri.SERIES_NAME, SUM(ffnc.UNREALIZED_APPRECIATION) AS UnrealizedAppreciation
FROM FUND_REPORTED_INFO fri
JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
JOIN FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc ON frh.HOLDING_ID = ffnc.HOLDING_ID
WHERE fri.YEAR = 2019 AND fri.QUARTER = 4
GROUP BY fri.SERIES_NAME
ORDER BY UnrealizedAppreciation DESC
LIMIT 4;
"""

# Connect to the db
conn = sqlite3.connect(db_path)

# Execute the SQL query, fetch the results into a df
df = pd.read_sql_query(sql_query, conn)

# close db connection
conn.close()

# Save the df to a csv file
df.to_csv('Medium8.csv', index=False)

print("CSV file has been saved.")
