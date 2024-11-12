import openai
import os
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from api_connection import openai_message_creator, query_openai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

# Set up database path
db_path = Path("data/sec_nport_data.db")

# try:
#     conn = sqlite3.connect(db_path)
#     sample_df = pd.read_sql_query("SELECT * FROM FUND_REPORTED_HOLDING LIMIT 5", conn)
#     conn.close()
#     print("Sample data from FUND_REPORTED_HOLDING table:")
#     print(sample_df)
# except Exception as e:
#     print(f"Error connecting to database or fetching sample data: {e}")


# Streamlit App Title
st.title("PIMCO Bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Define the system message for the OpenAI API

system_message_string = """
You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. Respond with **only the SQL query** and no additional explanation or formatting.

### Database Schema Overview (Specific):
1. **Main Tables and Key Columns**:
   - **FUND_REPORTED_INFO**:
     - Key columns: ACCESSION_NUMBER, SERIES_NAME, QUARTER, YEAR, TOTAL_ASSETS, NET_ASSETS.

   - **FUND_REPORTED_HOLDING**:
     - Key columns: ACCESSION_NUMBER, HOLDING_ID, ISSUER_NAME, CURRENCY_VALUE, CURRENCY_CODE.

2. **Quarter and Year Filtering**:
   - Interpret phrases like "quarter 1" or "quarter 2" using `QUARTER` and `YEAR` columns.
   - Example interpretations:
     - "Quarter 1 of 2022" translates to `QUARTER = q1 AND YEAR = 2022`.
     - "Quarter 4 of 2023" translates to `QUARTER = q4 AND YEAR = 2023`.

# 3. **Example Queries Using Exact Column Names**:

# **User Query Examples:**
# 1. **"show me wells fargo's holdings in quarter 2 of 2022"**
#     - SQL:
      ```sql
#     SELECT * FROM FUND_REPORTED_HOLDING WHERE ACCESSION_NUMBER IN (SELECT ACCESSION_NUMBER FROM FUND_REPORTED_INFO WHERE QUARTER = 'q2' AND YEAR = 2022) AND ISSUER_NAME LIKE '%Wells Fargo%'
#     ```

### Instructions:
- Use exact column names from the N-PORT dataset when constructing SQL queries.
- Return **only** the SQL query without any additional explanations or formatting.
- Do not include code blocks, comments, or any other text in your response.
"""










# system_message_string = """
# You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. Respond with **only the SQL query** and no additional explanation or formatting.

# ### Database Schema Overview (Specific):
# 1. **Main Tables and Key Columns**:
#    - **FUND_REPORTED_INFO**:
#      - Key columns: ACCESSION_NUMBER, SERIES_NAME, QUARTER, YEAR, TOTAL_ASSETS, NET_ASSETS.

#    - **FUND_REPORTED_HOLDING**:
#      - Key columns: ACCESSION_NUMBER, HOLDING_ID, ISSUER_NAME, CURRENCY_VALUE, CURRENCY_CODE.

# 2. **Quarter and Year Filtering**:
#    - Interpret phrases like "quarter 1" or "quarter 2" using `QUARTER` and `YEAR` columns.
#    - Example interpretations:
#      - "Quarter 1 of 2022" translates to `QUARTER = q1 AND YEAR = 2022`.
#      - "Quarter 4 of 2023" translates to `QUARTER = q4 AND YEAR = 2023`.

# ### Instructions:
# - Use exact column names from the N-PORT dataset when constructing SQL queries.
# - Return **only** the SQL query without any additional explanations or formatting.
# - Do not include code blocks, comments, or any other text in your response.
# """



# system_message_string = """
# You are generating SQL queries to extract information from N-PORT data for a user who does not know SQL. This user will ask questions in plain language, such as "What are the holdings for Fidelity in quarter 2 of 2022?" or "Show the most popular securities," and your task is to interpret these questions accurately. Users may not use exact table or column names, so focus on recognizing keywords and phrases to match questions to the appropriate tables and fields.

# ### Database Schema Overview (Specific):

# 1. **Main Tables and Key Columns**:
#    - **FUND_REPORTED_INFO**:
#      - Key columns: `ACCESSION_NUMBER`, `SERIES_NAME`, `QUARTER`, `YEAR`, `TOTAL_ASSETS`, `NET_ASSETS`.

#    - **FUND_REPORTED_HOLDING**:
#      - Key columns: `ACCESSION_NUMBER`, `HOLDING_ID`, `ISSUER_NAME`, `CURRENCY_VALUE`, `CURRENCY_CODE`.

#    - **INTEREST_RATE_RISK**:
#      - Key columns: `ACCESSION_NUMBER`, `INTEREST_RATE_RISK_ID`, `INTRST_RATE_CHANGE_1YR_DV01`, `INTRST_RATE_CHANGE_5YR_DV01`, etc.

# 2. **Quarter and Year Filtering**:
#    - Interpret phrases like "quarter 1" or "quarter 2" using `QUARTER` and `YEAR` columns.
#    - Example interpretations:
#      - "Quarter 1 of 2022" translates to `QUARTER = 1 AND YEAR = 2022`.
#      - "Quarter 4 of 2023" translates to `QUARTER = 4 AND YEAR = 2023`.

# 3. **Example Queries Using Exact Column Names**:

# **User Query Examples:**

# 1. **"What are the holdings for PIMCO Income Fund in quarter 2 of 2022?"**
#     - SQL:
#     ```sql
#     SELECT h.ISSUER_NAME, h.CURRENCY_VALUE, h.CURRENCY_CODE
#     FROM FUND_REPORTED_HOLDING h
#     JOIN FUND_REPORTED_INFO f ON h.ACCESSION_NUMBER = f.ACCESSION_NUMBER
#     WHERE f.SERIES_NAME = 'PIMCO Income Fund' AND f.QUARTER = 2 AND f.YEAR = 2022
#     LIMIT 10;
#     ```

# 2. **"Show me asset allocation changes for Fidelity Fund between quarter 4 of 2022 and quarter 1 of 2023"**
#     - SQL:
#     ```sql
#     SELECT h1.ISSUER_NAME, (h2.CURRENCY_VALUE - h1.CURRENCY_VALUE) AS allocation_change
#     FROM FUND_REPORTED_HOLDING h1
#     JOIN FUND_REPORTED_HOLDING h2 ON h1.ISSUER_NAME = h2.ISSUER_NAME
#     JOIN FUND_REPORTED_INFO f1 ON h1.ACCESSION_NUMBER = f1.ACCESSION_NUMBER
#     JOIN FUND_REPORTED_INFO f2 ON h2.ACCESSION_NUMBER = f2.ACCESSION_NUMBER
#     WHERE f1.SERIES_NAME = 'Fidelity Fund' AND f2.SERIES_NAME = 'Fidelity Fund'
#       AND f1.QUARTER = 4 AND f1.YEAR = 2022
#       AND f2.QUARTER = 1 AND f2.YEAR = 2023
#     LIMIT 10;
#     ```

# **Instructions**:
# - Use exact column names from the N-PORT dataset when constructing SQL queries.
# - Apply filtering based on `QUARTER` and `YEAR` columns without translating to dates.
# - Limit output by default (`LIMIT 10`) unless specified otherwise.
# """

# Streamed response emulator
def stream_response(response):
    if response:
        for word in response.split():
            yield word + " "
            time.sleep(0.05)
    else:
        yield "No response available."

# Function to execute SQL query on the database
def execute_sql_query(query, db_path):
    try:
        conn = sqlite3.connect(db_path)
        df_result = pd.read_sql_query(query, conn)
        conn.close()
        return df_result
    except Exception as e:
        st.error(f"Error executing the SQL query: {e}")
        return None

# Chat history display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input 
if prompt := st.chat_input("Enter your question about the database:"):
    refined_prompt = f"Generate an SQL query for this request: '{prompt}'. Return only the query."

    # Display user message in chat history
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate OpenAI messages and query the API
    messages = openai_message_creator(user_message_string=refined_prompt, system_message_string=system_message_string)
    sql_query = query_openai(messages)  # Generate SQL query
    print("Raw OpenAI Response:", sql_query)


    if sql_query:
        # Display the full model response before any cleaning
        st.session_state.messages.append({"role": "assistant", "content": f"Model's Full Response:\n{sql_query}"})
        st.write("Model's Full Response:")
        st.markdown(sql_query)  # Display the model response in Streamlit directly

        # Clean the response to remove any unwanted markdown or formatting
        cleaned_sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        print("Generated SQL query:")
        print(cleaned_sql_query)  # Print the query for inspection
        st.session_state.messages.append({"role": "assistant", "content": f"Generated SQL query:\n{cleaned_sql_query}"})

        # Execute the SQL query and display the result
        df_result = execute_sql_query(cleaned_sql_query, db_path)
        
        if df_result is not None:
            st.write("Query Results:")
            st.dataframe(df_result)  # Display results in Streamlit
    else:
        st.session_state.messages.append({"role": "assistant", "content": "No response available"})






# import streamlit as st
# import time
# from api_connection import openai_message_creator, query_openai
# from database_operations import create_engine_connection, save_to_database
# from data_loading import load_and_sample_data

# # Streamed response emulator
# def stream_response(response):
#     if response:  # Check if response is not None or empty
#         for word in response.split():
#             yield word + " "
#             time.sleep(0.05)
#     else:
#         yield "No response available."

# st.title("PIMCO Bot")

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# if prompt := st.chat_input("Enter your prompt:"):
#     st.chat_message("user").markdown(prompt)
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # Define system message here or externally
#     system_message = "You are generating SQL queries to extract information..."
#     messages = openai_message_creator(prompt, system_message)

#     # Query the OpenAI API for response
#     response_text = query_openai(messages) or "No response available"  # Fallback if response_text is None

#     with st.chat_message("assistant"):
#         response = st.write_stream(stream_response(response_text))
#     st.session_state.messages.append({"role": "assistant", "content": response_text})
