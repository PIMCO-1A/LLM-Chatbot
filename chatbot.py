import os
import sqlite3
import pandas as pd
import streamlit as st
import openai
from dotenv import load_dotenv
from pathlib import Path
from api_connection import openai_message_creator, query_openai, schema_to_string, process_prompt_for_quarter_year
from schema_loader import load_schema

# load env variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

# db path
db_path = Path("data/sec_nport_data_combined.db")

# Load the schema
schema_file_path = "data/data_schema2.txt"
schema = load_schema(schema_file_path)

# app title
st.title("PIMCO Bot")

# Example prompts and queries to guide chatbot behavior
example_prompts_and_queries = {
    "easy": [
        {
            "question": "What is the total net asset value of PIMCO Income Fund for Q1 2023?",
            "query": """
            SELECT NET_ASSETS
            FROM FUND_REPORTED_INFO
            WHERE SERIES_NAME = 'PIMCO Income Fund' AND YEAR = 2023 AND QUARTER = 1;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "What is the total net asset value of PIMCO Income Fund for Q1 2023?" needs these tables = [FUND_REPORTED_INFO], so we don't need JOIN.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we don't need JOIN and don't need nested queries, then the SQL query can be classified as "EASY".
            """,
            "schema_links": "FUND_REPORTED_INFO.NET_ASSETS, FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, PIMCO Income Fund, 2023, 1"
        },
        {
            "question": "List all issuers and their corresponding LEIs for holdings in Q2 2022.",
            "query": """
            SELECT ISSUER_NAME, ISSUER_LEI
            FROM FUND_REPORTED_HOLDING
            WHERE YEAR = 2022 AND QUARTER = 2;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "List all issuers and their corresponding LEIs for holdings in Q2 2022." needs these tables = [FUND_REPORTED_HOLDING], so we don't need JOIN.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we don't need JOIN and don't need nested queries, then the SQL query can be classified as "EASY".
            """,
            "schema_links": "FUND_REPORTED_HOLDING.ISSUER_NAME, FUND_REPORTED_HOLDING.ISSUER_LEI, FUND_REPORTED_HOLDING.YEAR, FUND_REPORTED_HOLDING.QUARTER, 2022, 2"
        },
        {
            "question": "Which securities in Q1 2022 have unrealized appreciation or depreciation?",
            "query": """
            SELECT ISSUER_NAME, UNREALIZED_APPRECIATION
            FROM FUT_FWD_NONFOREIGNCUR_CONTRACT
            WHERE YEAR = 2022 AND QUARTER = 1;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Which securities in Q1 2022 have unrealized appreciation or depreciation?" needs these tables = [FUT_FWD_NONFOREIGNCUR_CONTRACT], so we don't need JOIN.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we don't need JOIN and don't need nested queries, then the SQL query can be classified as "EASY".
            """,
            "schema_links": "FUT_FWD_NONFOREIGNCUR_CONTRACT.ISSUER_NAME, FUT_FWD_NONFOREIGNCUR_CONTRACT.UNREALIZED_APPRECIATION, FUT_FWD_NONFOREIGNCUR_CONTRACT.YEAR, FUT_FWD_NONFOREIGNCUR_CONTRACT.QUARTER, 2022, 1"
        },
        {
            "question": "What are the total net assets for all funds in Q2 2023?",
            "query": """
            SELECT SUM(NET_ASSETS)
            FROM FUND_REPORTED_INFO
            WHERE YEAR = 2023 AND QUARTER = 2;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "What are the total net assets for all funds in Q2 2023?" needs this table = [FUND_REPORTED_INFO], so we don't need JOINs.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we don't need JOINs and don't need nested queries, then the SQL query can be classified as "EASY."
            """,
            "schema_links": "FUND_REPORTED_INFO.NET_ASSETS, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, 2023, 2"
        },
        {
            "question": "Find the maturity dates for repurchase agreements in 2022 Q3.",
            "query": """
            SELECT MATURITY_DATE
            FROM REPURCHASE_AGREEMENT
            WHERE YEAR = 2022 AND QUARTER = 3;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Find the maturity dates for repurchase agreements in 2022 Q3" needs these tables = [REPURCHASE_AGREEMENT], so we don't need JOIN.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we don't need JOIN and don't need nested queries, then the SQL query can be classified as "EASY".
            """,
            "schema_links": "REPURCHASE_AGREEMENT.MATURITY_DATE, REPURCHASE_AGREEMENT.YEAR, REPURCHASE_AGREEMENT.QUARTER, 2022, 3"
        },
        {
            "question": "What is the currency value of holdings for Tennant Co in Q4 2022?",
            "query": """
            SELECT CURRENCY_VALUE
            FROM FUND_REPORTED_HOLDING
            WHERE ISSUER_NAME = 'Tennant Co' AND YEAR = 2022 AND QUARTER = 4;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "What is the currency value of holdings for Tennant Co in Q4 2022?" needs these tables = [FUND_REPORTED_HOLDING], so we don't need JOIN.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we don't need JOIN and don't need nested queries, then the SQL query can be classified as "EASY".
            """,
            "schema_links": "FUND_REPORTED_HOLDING.CURRENCY_VALUE, FUND_REPORTED_HOLDING.ISSUER_NAME, FUND_REPORTED_HOLDING.YEAR, FUND_REPORTED_HOLDING.QUARTER, Tennant Co, 2022, 4"
        }
    ],
    "medium": [
        {
            "question": "What are the cash holdings of the Vanguard Total Bond Market Index Fund as of the latest reporting date?",
            "query": """
            SELECT frh.BALANCE AS CashHoldings
            FROM FUND_REPORTED_HOLDING frh
            JOIN FUND_REPORTED_INFO fri ON frh.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
            JOIN SUBMISSION sub ON fri.ACCESSION_NUMBER = sub.ACCESSION_NUMBER
            WHERE fri.SERIES_NAME LIKE '%Vanguard Total Bond Market Index Fund%'
            ORDER BY sub.REPORT_DATE DESC
            LIMIT 1;
            """,
            "reasoning": """
            Let’s think step by step. The SQL query for the question "What are the cash holdings of the Vanguard Total Bond Market Index Fund as of the latest reporting date?" needs these tables = [FUND_REPORTED_HOLDING, FUND_REPORTED_INFO, SUBMISSION], so we need JOIN.
            Plus, it doesn’t require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don’t need nested queries, then the SQL query can be classified as "MEDIUM".
            """,
            "schema_links": "FUND_REPORTED_INFO.ACCESSION_NUMBER = FUND_REPORTED_HOLDING.ACCESSION_NUMBER, SUBMISSION.ACCESSION_NUMBER = fri.ACCESSION_NUMBER, FUND_REPORTED_HOLDING.BALANCE, FUND_REPORTED_INFO.SERIES_NAME, SUBMISSION.REPORT_DATE, Vanguard Total Bond Market Index Fund"
        },
        {
            "question": "Compare derivative allocation trends for Fidelity funds from 2020 to 2023.",
            "query": """
            SELECT fri.SERIES_NAME, ffnc.YEAR, SUM(ffnc.NOTIONAL_AMOUNT) / SUM(fri.TOTAL_ASSETS) * 100 AS DerivativeAllocationPercentage
            FROM FUND_REPORTED_INFO fri
            JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
            JOIN FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc ON frh.HOLDING_ID = ffnc.HOLDING_ID
            WHERE fri.SERIES_NAME LIKE '%Fidelity%' AND ffnc.YEAR BETWEEN 2020 AND 2023
            GROUP BY fri.SERIES_NAME, ffnc.YEAR
            ORDER BY fri.SERIES_NAME, ffnc.YEAR;
            """,
            "reasoning": """
            Let’s think step by step. The SQL query for the question "Compare derivative allocation trends for Fidelity funds from 2020 to 2023" needs these tables = [FUND_REPORTED_INFO, FUND_REPORTED_HOLDING, FUT_FWD_NONFOREIGNCUR_CONTRACT], so we need JOINs on ACCESSION_NUMBER and HOLDING_ID.
            Plus, it doesn’t require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM."
            """,
            "schema_links": "FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.TOTAL_ASSETS, FUND_REPORTED_HOLDING.HOLDING_ID, FUT_FWD_NONFOREIGNCUR_CONTRACT.NOTIONAL_AMOUNT, FUT_FWD_NONFOREIGNCUR_CONTRACT.YEAR, FUND_REPORTED_INFO.ACCESSION_NUMBER = FUND_REPORTED_HOLDING.ACCESSION_NUMBER, FUND_REPORTED_HOLDING.HOLDING_ID = FUT_FWD_NONFOREIGNCUR_CONTRACT.HOLDING_ID, %Fidelity%, 2020, 2023"
        },
        {
            "question": "What is the currency-wise allocation of restricted securities in Q1 2023?",
            "query": """
            SELECT frh.CURRENCY_CODE,
                SUM(frh.CURRENCY_VALUE) AS TotalRestrictedValue,
                (SUM(frh.CURRENCY_VALUE) / SUM(fri.TOTAL_ASSETS)) * 100 AS RestrictedPercentage
            FROM FUND_REPORTED_HOLDING frh
            JOIN FUND_REPORTED_INFO fri ON frh.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
            WHERE frh.IS_RESTRICTED_SECURITY = 'Y' AND fri.YEAR = 2023 AND fri.QUARTER = 1
            GROUP BY frh.CURRENCY_CODE;
            """,
            "reasoning": """
            Let’s think step by step. The SQL query for the question "What is the currency-wise allocation of restricted securities in Q1 2023?" needs these tables = [FUND_REPORTED_HOLDING, FUND_REPORTED_INFO], so we need JOIN on ACCESSION_NUMBER.
            Plus, it doesn’t require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM."
            """,
            "schema_links": "FUND_REPORTED_HOLDING.CURRENCY_CODE, FUND_REPORTED_HOLDING.CURRENCY_VALUE, FUND_REPORTED_HOLDING.IS_RESTRICTED_SECURITY, FUND_REPORTED_INFO.TOTAL_ASSETS, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, FUND_REPORTED_HOLDING.ACCESSION_NUMBER = FUND_REPORTED_INFO.ACCESSION_NUMBER, Y, 2023, 1"
        }
    ]
}


# initialize chat history and persistent query log
if "messages" not in st.session_state:
    st.session_state.messages = []
if "persistent_query_log" not in st.session_state:
    st.session_state.persistent_query_log = []

# function to execute SQL query w debugging
def execute_sql_query(query, db_path):
    """
    Executes the provided SQL query against the SQLite database at db_path.
    Logs the query being executed for debugging purposes. If there's an error,
    it attempts to fix the query.
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
        # Generate the query-fixing prompt using the given details
        query_fixing_prompt = f"""
        **Task Description:**
        You are an SQL database expert tasked with correcting a SQL query. A previous attempt to run a query did not yield the correct results,
        either due to errors in execution or because the result returned was empty or unexpected. Your role is to analyze the error based on 
        the provided database schema and the details of the failed execution, and then provide a corrected version of the SQL query. 

        **Procedure:**
        1. Review Database Schema
        - Examine the following schema details to understand the database structure:
        {schema_to_string(schema)}
        2. Review Example User Questions, Queries, and Explanations
        - Examine the following examples as a reference to guide your corrected response:
            - Easy Questions: {[example for example in example_prompts_and_queries['easy']]}
            - Medium Questions: {[example for example in example_prompts_and_queries['medium']]}
        3. Analyze Query Requirements:
        - Original Question: Consider what information the query is supposed to retrieve.
        - Executed SQL Query: Review the SQL query that was previously executed and led to an error or incorrect result.
        - Execution Result: Analyze the outcome of the executed query to identify why it failed (e.g., syntax errors, incorrect column references, logical mistakes).
        4. Adhere to Rules:
        - Remember the rules you must follow:
            - Only use `QUARTER` and `YEAR` in the SQL query, do not use any specific dates. If the user question contains a specific date, please convert this to the appropriate year and quarter.
            - Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
            - All queries must be valid to access a SQLite database (e.g., use the command LIMIT instead of FETCH)
            - When you start the Explanation you need to put “Explanation:” before it
        5. Correct the Query:
        - Modify the SQL query to address the identified issues, ensuring it correctly fetches the requested data according to the database schema and query requirements.

        **Output Format**
        [SQL Query]
        Explanation: [Explanation of SQL Query]
        
        Based on the question, table schema, and previous query, analyze the result to fix the query and make it valid and executable.
        """
        
        # Query OpenAI to fix the query
        fixing_response = query_openai(openai_message_creator(
            user_message_string=query_fixing_prompt,
            system_message_string="You are an expert SQL assistant. Review the SQL query for errors and provide corrections with explanations."
        ))
        
        if fixing_response:
            # Parse the response to extract the suggested corrected query and explanation
            if "Explanation:" in fixing_response:
                fixed_query, explanation = fixing_response.split("Explanation:", 1)
                fixed_query = fixed_query.strip()
                explanation = explanation.strip()
            else:
                fixed_query = fixing_response.strip()
                explanation = "No explanation provided."
            
            # Return the fixed query and explanation
            return fixed_query, explanation
        
        # If no response, return the error message
        return f"Error: {e}", None

# function to validate SQL query
def validate_sql_query(query):
    """
    Validates that the SQL query is well-formed and safe to execute.
    """
    # Basic validation to check for SELECT and FROM statements
    if "SELECT" in query and "FROM" in query and ";" in query:
        return True
    return False

# display persistent query log
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

# user input
if prompt := st.chat_input("Enter your question about the database:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process specific dates or date ranges in the prompt
    refined_prompt = process_prompt_for_quarter_year(prompt)
    refined_prompt = f"Generate an SQL query for this request: '{refined_prompt}'. Return only the query and an explanation."

    # Generate OpenAI messages with schema and examples
    system_message_string = f"""
    **Task Description:**
    You are an assistant that generates SQL queries based on user questions related to the SEC N-PORT dataset. 

    **Background:**
    N-PORT filings contain detailed reports submitted by registered investment companies, including mutual funds and exchange-traded funds (ETFs), which disclose their portfolio holdings on a monthly basis. 
    These filings provide transparency into the asset composition, performance, and risk exposures of these funds, offering valuable insights for investors, regulators, and researchers.
    Your goal is to write and execute SQL queries on a SQLite database to answer natural language questions asked by the user. 

    **Procedure**
    1. Review Database Schema
    - Examine the following schema details to understand the database structure:
    {schema_to_string(schema)}
    2. Review Example User Questions, Queries, and Explanations
    - Examine the following examples as a reference to guide your response:
        - Easy Questions: {[example for example in example_prompts_and_queries['easy']]}
        - Medium Questions: {[example for example in example_prompts_and_queries['medium']]}
    3. Analyze User Question
    - Carefully identify what the user wants to know
    - Understand the intent behind the question 
    - Determine how the SQL query should be structured to accurately access a SQLite database

    **Output Format:**
    [SQL Query]
    Explanation: [Explanation of SQL Query]

    **Rules:**
    1. Only use `QUARTER` and `YEAR` in the SQL query, do not use any specific dates. If the user question contains a specific date, please convert this to the appropriate year and quarter.
    2. Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
    3. All queries must be valid to access a SQLite database (e.g., use the command LIMIT instead of FETCH)
    4. When you start the Explanation you need to put “Explanation:” before it
    """
    messages = openai_message_creator(user_message_string=refined_prompt, system_message_string=system_message_string, schema=schema)

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








