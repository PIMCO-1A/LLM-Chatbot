import os
import sqlite3
import pandas as pd
import streamlit as st
import openai
from dotenv import load_dotenv
from pathlib import Path
from api_connection import openai_message_creator, query_openai, schema_to_string, process_prompt_for_quarter_year
from data_loading import load_schema

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

# Set up database path
db_path = Path("data/sec_nport_data_subset.db")

# Load the schema
schema_file_path = "Table_Schema.txt"
schema = load_schema(schema_file_path)

# Streamlit App Title
st.title("PIMCO Bot")

# Initialize chat history and persistent query log
if "messages" not in st.session_state:
    st.session_state.messages = []
if "persistent_query_log" not in st.session_state:
    st.session_state.persistent_query_log = []

# Function to execute SQL query with debugging
def execute_sql_query(query, db_path):
    """
    Executes the provided SQL query against the SQLite database at db_path.
    Logs the query being executed for debugging purposes.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        
        # Debugging: Print the SQL query
        print(f"Executing Query:\n{query}")
        
        # Execute the query and fetch the result as a DataFrame
        df_result = pd.read_sql_query(query, conn)
        
        # Close the connection
        conn.close()
        
        return df_result
    except Exception as e:
        # Log the error
        print(f"Error executing the SQL query: {e}")
        return None

# Function to validate SQL query
def validate_sql_query(query):
    """
    Validates that the SQL query is well-formed and safe to execute.
    """
    # Basic validation to check for SELECT and FROM statements
    if "SELECT" in query and "FROM" in query and ";" in query:
        return True
    return False

# Display persistent query log
if "persistent_query_log" in st.session_state and st.session_state.persistent_query_log:
    for query_record in st.session_state.persistent_query_log:
        st.write("#### Question")
        st.markdown(query_record["question"])
        st.write("#### SQL Query")
        st.code(query_record["query"], language="sql")
        st.write("#### Explanation")
        st.markdown(query_record["explanation"])
        st.write("#### Results")
        st.dataframe(query_record["results"])

# User input
if prompt := st.chat_input("Enter your question about the database:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process specific dates or date ranges in the prompt
    refined_prompt = process_prompt_for_quarter_year(prompt)
    refined_prompt = f"Generate an SQL query for this request: '{refined_prompt}'. Return only the query and an explanation."

    # Generate OpenAI messages with schema
    system_message_string = f"""
    You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. 
    Use the provided database schema to ensure accurate queries. Respond in the following format:
    SQL Query:
    [Generated SQL Query]

    Explanation:
    [Explanation of the Query]

    Rules:
    1. Only use `QUARTER` and `YEAR` in the SQL query. Do not use any specific dates. Use the `QUARTER` and `YEAR` columns directly, and do not use any functions like QUARTER() or YEAR().
    2. Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
    """
    system_message_with_schema = f"{system_message_string}\n\n### Schema Details:\n{schema_to_string(schema)}"
    messages = openai_message_creator(user_message_string=refined_prompt, system_message_string=system_message_with_schema, schema=schema)

    response = query_openai(messages)

    if response:
        # Clean the response to extract the SQL query and explanation
        if "Explanation:" in response:
            sql_query, explanation = response.split("Explanation:", 1)
            sql_query = sql_query.split("SQL Query:")[-1].strip()  # Extract only the query text
            explanation = explanation.strip()
        else:
            sql_query = response.splitlines()[0].strip()
            explanation = "No explanation provided."

        # Clean the query before executing it
        cleaned_sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        print(f"Cleaned SQL Query:\n{cleaned_sql_query}")

        # Validate the cleaned query
        if validate_sql_query(cleaned_sql_query):
            # Execute the cleaned query
            df_result = execute_sql_query(cleaned_sql_query, db_path)
            
            if df_result is not None:
                # Save query, explanation, and results to persistent query log
                query_record = {
                    "question": prompt,
                    "query": cleaned_sql_query,
                    "explanation": explanation,
                    "results": df_result
                }
                st.session_state.persistent_query_log.append(query_record)

                # Display SQL query, explanation, and results
                st.write("#### Question")
                st.markdown(query_record["question"])
                st.write("#### SQL Query")
                st.code(query_record["query"], language="sql")
                st.write("#### Explanation")
                st.markdown(query_record["explanation"])
                st.write("#### Results")
                st.dataframe(query_record["results"])
            else:
                st.error("Failed to execute the query. Check the logs for details.")
        else:
            # If the query is invalid, show an error message
            st.error("Invalid SQL query generated. Please review.")
    else:
        st.error("No response generated. Please try again.")























# import os
# import sqlite3
# import pandas as pd
# import streamlit as st
# import openai
# from dotenv import load_dotenv
# from pathlib import Path
# from api_connection import openai_message_creator, query_openai, schema_to_string, process_prompt_for_quarter_year
# from data_loading import load_schema

# # Load environment variables
# load_dotenv()
# API_KEY = os.getenv("OPENAI_API_KEY")
# openai.api_key = API_KEY

# # Set up database path
# db_path = Path("data/sec_nport_data_subset.db")

# # loading schema
# schema_file_path = "Table_Schema.txt"
# schema = load_schema(schema_file_path)

# # app title 
# st.title("PIMCO Bot")

# # Initialize chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "query_history" not in st.session_state:
#     st.session_state.query_history = []

# # Define the system message for the OpenAI API
# system_message_string = """
# You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. 
# Use the provided database schema to ensure accurate queries. Respond in the following format:
# SQL Query:
# [Generated SQL Query]

# Explanation:
# [Explanation of the Query]

# Rules:
# 1. Only use `QUARTER` and `YEAR` in the SQL query. Do not use any specific dates. Use the `QUARTER` and `YEAR` columns directly, and do not use any functions like QUARTER() or YEAR().
# 2. Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
# """

# # Chat history display
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # Display query history at the top of the app
# st.markdown("### Query History")
# for query_record in st.session_state.query_history:
#     st.markdown(f"- **SQL Query:** `{query_record['query']}`")
#     st.markdown(f"  **Explanation:** {query_record['explanation']}")
#     st.markdown(f"  **Results:**")
#     st.dataframe(query_record["results"])

# # Function to execute SQL query with debugging
# def execute_sql_query(query, db_path):
#     """
#     Executes the provided SQL query against the SQLite database at db_path.
#     Logs the query being executed for debugging purposes.
#     """
#     try:
#         # Connect to the SQLite database
#         conn = sqlite3.connect(db_path)
        
#         # Debugging: Print the SQL query
#         print(f"Executing Query:\n{query}")
        
#         # Execute the query and fetch the result as a DataFrame
#         df_result = pd.read_sql_query(query, conn)
        
#         # Close the connection
#         conn.close()
        
#         return df_result
#     except Exception as e:
#         # Log the error
#         print(f"Error executing the SQL query: {e}")
#         return None

# # Function to validate SQL query
# def validate_sql_query(query):
#     """
#     Validates that the SQL query is well-formed and safe to execute.
#     """
#     # Basic validation to check for SELECT and FROM statements
#     if "SELECT" in query and "FROM" in query and ";" in query:
#         return True
#     return False

# # User input
# if prompt := st.chat_input("Enter your question about the database:"):
#     # Process specific dates or date ranges in the prompt
#     refined_prompt = process_prompt_for_quarter_year(prompt)
#     refined_prompt = f"Generate an SQL query for this request: '{refined_prompt}'. Return only the query and an explanation."

#     # Display user message in chat history
#     st.chat_message("user").markdown(prompt)
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # Generate OpenAI messages with schema
#     system_message_with_schema = f"{system_message_string}\n\n### Schema Details:\n{schema_to_string(schema)}"
#     messages = openai_message_creator(user_message_string=refined_prompt, system_message_string=system_message_with_schema, schema=schema)

#     response = query_openai(messages)

#     if response:

#         # Clean the response to extract the SQL query and explanation
#         if "Explanation:" in response:
#             sql_query, explanation = response.split("Explanation:", 1)
#             sql_query = sql_query.split("SQL Query:")[-1].strip()  # Extract only the query text
#             explanation = explanation.strip()
#         else:
#             sql_query = response.splitlines()[0].strip()
#             explanation = "No explanation provided."

#         # Clean the query before executing it
#         cleaned_sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
#         print(f"Cleaned SQL Query:\n{cleaned_sql_query}")

#         # Validate the cleaned query
#         if validate_sql_query(cleaned_sql_query):
#             # Execute the cleaned query
#             df_result = execute_sql_query(cleaned_sql_query, db_path)
            
#             if df_result is not None:
#                 # Save query, explanation, and results to history
#                 st.session_state.query_history.append({
#                     "query": cleaned_sql_query,
#                     "explanation": explanation,
#                     "results": df_result
#                 })

#                 # Display results
#                 st.write("Query Results:")
#                 st.dataframe(df_result)
#             else:
#                 st.error("Failed to execute the query. Check the logs for details.")
#         else:
#             # If the query is invalid, show an error message
#             st.error("Invalid SQL query generated. Please review.")
#             print("Invalid SQL query detected. Aborting execution.")
#     else:
#         st.session_state.messages.append({"role": "assistant", "content": "No response available."})















