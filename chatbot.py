import os
import sqlite3
import pandas as pd
import streamlit as st
import openai
from dotenv import load_dotenv
from pathlib import Path
from api_connection import openai_message_creator, query_openai, schema_to_string
from data_loading import load_schema

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

# Set up database path
db_path = Path("data/sec_nport_data.db")

# Load the schema
schema_file_path = "Table_Schema.txt"
schema = load_schema(schema_file_path)

# Streamlit App Title
st.title("PIMCO Bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Define the system message for the OpenAI API
system_message_string = """
You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. 
Use the provided database schema to ensure accurate queries. Respond with **only the SQL query** and an **explanation of the query**.
"""

# Prompt templates for schema linking, classification, and correction
classification_prompt = """
Classify the given question into one of the following categories:
- EASY: Simple SELECT statement without JOINs or subqueries.
- NON-NESTED: Query requires JOINs but no nested subqueries.
- NESTED: Query involves nested subqueries or complex logic.
Return the category as 'EASY', 'NON-NESTED', or 'NESTED'.
"""

schema_linking_prompt = """
Identify the relevant tables and columns from the schema to generate a valid SQL query for the given question. 
List the schema links as: [table1.column1, table2.column2, ...].
"""

correction_prompt = """
Check the given SQL query for errors based on the database schema, including column names, table relationships, and syntax. 
If there are errors, provide the corrected query. If there are no errors, return 'No errors found.'
"""

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

# Function to generate schema links
def create_schema_links(schema):
    # Placeholder logic for creating schema links (can be dynamic)
    schema_links = "Foreign_keys = [...]"  # Update this based on schema relationships
    return schema_links

# Chat history display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Enter your question about the database:"):
    refined_prompt = f"Generate an SQL query for this request: '{prompt}'. Return only the query and an explanation."

    # Display user message in chat history
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate OpenAI messages with schema links and classification
    schema_links = create_schema_links(schema)
    system_message_with_schema = f"{system_message_string}\n\n### Schema Details:\n{schema_to_string(schema)}\n### Schema Links:\n{schema_links}\n"

    # Classification prompt
    classification_messages = openai_message_creator(user_message_string=prompt, system_message_string=classification_prompt, schema=schema)
    query_classification = query_openai(classification_messages)
    print(f"Query Classification: {query_classification}")

    # Main SQL generation prompt
    messages = openai_message_creator(user_message_string=refined_prompt, system_message_string=system_message_with_schema, schema=schema)
    response = query_openai(messages)

    if response:
        # Display the full model response
        st.session_state.messages.append({"role": "assistant", "content": f"Model's Full Response:\n{response}"})
        st.write("Model's Full Response:")
        st.markdown(response)

        # Clean the response to extract the SQL query and explanation
        if "Explanation:" in response:
            sql_query, explanation = response.split("Explanation:", 1)
            sql_query = sql_query.strip()
            explanation = explanation.strip()
        else:
            sql_query = response.strip()
            explanation = "No explanation provided."

        st.session_state.messages.append({"role": "assistant", "content": f"Generated SQL query:\n{sql_query}"})
        st.session_state.messages.append({"role": "assistant", "content": f"Query Explanation:\n{explanation}"})
        st.write("Generated SQL Query:")
        st.code(sql_query)
        st.write("Query Explanation:")
        st.markdown(explanation)

        # Execute the SQL query and display the result
        df_result = execute_sql_query(sql_query, db_path)
        if df_result is not None:
            st.write("Query Results:")
            st.dataframe(df_result)
    else:
        st.session_state.messages.append({"role": "assistant", "content": "No response available."})



















# import os
# import sqlite3
# import pandas as pd
# import streamlit as st
# import openai
# from dotenv import load_dotenv
# from pathlib import Path
# from api_connection import openai_message_creator, query_openai, schema_to_string
# from data_loading import load_schema

# # Load environment variables
# load_dotenv()
# API_KEY = os.getenv("OPENAI_API_KEY")
# openai.api_key = API_KEY

# # Set up database path
# db_path = Path("data/sec_nport_data_subset.db")

# # Load the schema
# schema_file_path = "Table_Schema.txt"
# schema = load_schema(schema_file_path)

# # Streamlit App Title
# st.title("PIMCO Bot")

# # Initialize chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Define the system message for the OpenAI API
# system_message_string = """
# You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. 
# Use the provided database schema to ensure accurate queries. Respond with **only the SQL query** and an **explanation of the query**.
# """

# # Streamed response emulator
# def stream_response(response):
#     if response:
#         for word in response.split():
#             yield word + " "
#     else:
#         yield "No response available."

# # Function to execute SQL query on the database
# def execute_sql_query(query, db_path):
#     try:
#         conn = sqlite3.connect(db_path)
#         df_result = pd.read_sql_query(query, conn)
#         conn.close()
#         return df_result
#     except Exception as e:
#         st.error(f"Error executing the SQL query: {e}")
#         return None

# # Chat history display
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # User input 
# if prompt := st.chat_input("Enter your question about the database:"):
#     refined_prompt = f"Generate an SQL query for this request: '{prompt}'. Return only the query."

#     # Display user message in chat history
#     st.chat_message("user").markdown(prompt)
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # Generate OpenAI messages with schema
#     messages = openai_message_creator(user_message_string=refined_prompt, system_message_string=system_message_string, schema=schema)
#     sql_query = query_openai(messages)  # Generate SQL query
#     print("Raw OpenAI Response:", sql_query)

#     if sql_query:
#         # Display the full model response before any cleaning
#         st.session_state.messages.append({"role": "assistant", "content": f"Model's Full Response:\n{sql_query}"})
#         st.write("Model's Full Response:")
#         st.markdown(sql_query)  # Display the model response in Streamlit directly

#         # Clean the response to remove any unwanted formatting
#         cleaned_sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
#         print("Generated SQL query:")
#         print(cleaned_sql_query)  # Print the query for inspection
#         st.session_state.messages.append({"role": "assistant", "content": f"Generated SQL query:\n{cleaned_sql_query}"})

#         # Execute the SQL query and display the result
#         df_result = execute_sql_query(cleaned_sql_query, db_path)
        
#         if df_result is not None:
#             st.write("Query Results:")
#             st.dataframe(df_result)  # Display results in Streamlit
#     else:
#         st.session_state.messages.append({"role": "assistant", "content": "No response available"})
