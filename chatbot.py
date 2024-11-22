import os
import sqlite3
import pandas as pd
import streamlit as st
import openai
from dotenv import load_dotenv
from pathlib import Path
from api_connection import openai_message_creator, query_openai, schema_to_string, process_prompt_for_quarter_year
from data_loading import load_schema

# load env variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

# db path
db_path = Path("data/sec_nport_data_subset.db")

# Load the schema
schema_file_path = "Table_Schema.txt"
schema = load_schema(schema_file_path)

# app title
st.title("PIMCO Bot")

# Example prompts and queries to guide chatbot behavior
example_prompts_and_queries = [
    {
        "question": "Find all fund-reported holdings where the issuer name contains 'Wells Fargo' in Quarter 1 of 2024.",
        "query": """
        SELECT *
        FROM FUND_REPORTED_HOLDING
        WHERE ISSUER_NAME LIKE '%Wells Fargo%' AND YEAR = 2024 AND QUARTER = 1;
        """
    },
    {
        "question": "Retrieve the LEI and total liabilities of all funds reported in Quarter 3 of 2023.",
        "query": """
        SELECT SERIES_LEI, TOTAL_LIABILITIES
        FROM FUND_REPORTED_INFO
        WHERE YEAR = 2023 AND QUARTER = 3;
        """
    },
    {
        "question": "List all borrower names with an aggregate value greater than $1,000,000 in Quarter 2 of 2022.",
        "query": """
        SELECT NAME, AGGREGATE_VALUE
        FROM BORROWER
        WHERE AGGREGATE_VALUE > 1000000 AND YEAR = 2022 AND QUARTER = 2;
        """
    },
    {
        "question": "Find the interest rate risk changes for 1-year maturity reported in Quarter 4 of 2021.",
        "query": """
        SELECT INTRST_RATE_CHANGE_1YR_DV01, INTRST_RATE_CHANGE_1YR_DV100
        FROM INTEREST_RATE_RISK
        WHERE YEAR = 2021 AND QUARTER = 4;
        """
    },
    {
        "question": "Retrieve the top 10 fund holdings by balance in Quarter 3 of 2020, sorted in descending order.",
        "query": """
        SELECT ISSUER_NAME, BALANCE
        FROM FUND_REPORTED_HOLDING
        WHERE YEAR = 2020 AND QUARTER = 3
        ORDER BY BALANCE DESC
        LIMIT 10;
        """
    },
    {
        "question": "List the names of borrowers who provided collateral valued over $500,000 in Quarter 1 of 2023.",
        "query": """
        SELECT NAME, COLLATERAL
        FROM BORROW_AGGREGATE
        WHERE COLLATERAL > 500000 AND YEAR = 2023 AND QUARTER = 1;
        """
    },
    {
        "question": "Find the cumulative unrealized appreciation for all derivative instruments in Quarter 2 of 2024.",
        "query": """
        SELECT SUM(UNREALIZED_APPRECIATION) AS TOTAL_UNREALIZED_APPRECIATION
        FROM OTHER_DERIV
        WHERE YEAR = 2024 AND QUARTER = 2;
        """
    },
    {
        "question": "List the fund-reported holdings with a balance greater than 1% of net assets in Quarter 4 of 2022.",
        "query": """
        SELECT ISSUER_NAME, BALANCE, PERCENTAGE
        FROM FUND_REPORTED_HOLDING
        WHERE PERCENTAGE > 1 AND YEAR = 2022 AND QUARTER = 4;
        """
    },
    {
        "question": "Retrieve the repurchase agreements with maturity dates in Quarter 3 of 2023.",
        "query": """
        SELECT TRANSACTION_TYPE, REPURCHASE_RATE, MATURITY_DATE
        FROM REPURCHASE_AGREEMENT
        WHERE YEAR = 2023 AND QUARTER = 3;
        """
    },
    {
        "question": "Find the number of fund-reported holdings by currency for Quarter 1 of 2021.",
        "query": """
        SELECT CURRENCY_CODE, COUNT(*) AS HOLDING_COUNT
        FROM FUND_REPORTED_HOLDING
        WHERE YEAR = 2021 AND QUARTER = 1
        GROUP BY CURRENCY_CODE;
        """
    },
    {
        "question": "Retrieve the names of counterparties for securities lending with non-cash collateral in Quarter 2 of 2023.",
        "query": """
        SELECT NAME, NON_CASH_COLLATERAL_VALUE
        FROM SECURITIES_LENDING
        WHERE IS_NON_CASH_COLLATERAL = 'Yes' AND YEAR = 2023 AND QUARTER = 2;
        """
    },
    {
        "question": "List the total realized and unrealized gains for derivatives in Quarter 4 of 2020.",
        "query": """
        SELECT SUM(NET_REALIZED_GAIN_MON1 + NET_REALIZED_GAIN_MON2 + NET_REALIZED_GAIN_MON3) AS TOTAL_REALIZED_GAIN,
               SUM(NET_UNREALIZED_AP_MON1 + NET_UNREALIZED_AP_MON2 + NET_UNREALIZED_AP_MON3) AS TOTAL_UNREALIZED_GAIN
        FROM MONTHLY_RETURN_CAT_INSTRUMENT
        WHERE YEAR = 2020 AND QUARTER = 4;
        """
    },
    {
        "question": "Find the LEI and assets for all funds with net assets greater than $10,000,000 in Quarter 3 of 2022.",
        "query": """
        SELECT SERIES_LEI, NET_ASSETS
        FROM FUND_REPORTED_INFO
        WHERE NET_ASSETS > 10000000 AND YEAR = 2022 AND QUARTER = 3;
        """
    },
    {
        "question": "List all debt securities in default during Quarter 2 of 2021.",
        "query": """
        SELECT HOLDING_ID, COUPON_TYPE, ANNUALIZED_RATE
        FROM DEBT_SECURITY
        WHERE IS_DEFAULT = 'Yes' AND YEAR = 2021 AND QUARTER = 2;
        """
    },
    {
        "question": "Retrieve the total returns for all classes during Quarter 1 of 2023.",
        "query": """
        SELECT CLASS_ID, (MONTHLY_TOTAL_RETURN1 + MONTHLY_TOTAL_RETURN2 + MONTHLY_TOTAL_RETURN3) AS TOTAL_RETURN
        FROM MONTHLY_TOTAL_RETURN
        WHERE YEAR = 2023 AND QUARTER = 1;
        """
    },
    {
        "question": "Find the issuer name, balance, and percentage of holdings exceeding 5% of net assets for funds with total assets over $100,000,000 in Quarter 2 of 2023.",
        "query": """
        SELECT FRH.ISSUER_NAME, FRH.BALANCE, FRH.PERCENTAGE
        FROM FUND_REPORTED_HOLDING FRH
        JOIN FUND_REPORTED_INFO FRI ON FRH.ACCESSION_NUMBER = FRI.ACCESSION_NUMBER
        WHERE FRI.TOTAL_ASSETS > 100000000 AND FRH.PERCENTAGE > 5 AND FRH.YEAR = 2023 AND FRH.QUARTER = 2;
        """
    },
    {
        "question": "List all fund-reported holdings with unrealized depreciation (negative unrealized appreciation) in Quarter 4 of 2021, sorted by descending depreciation.",
        "query": """
        SELECT ISSUER_NAME, UNREALIZED_APPRECIATION
        FROM OTHER_DERIV
        WHERE UNREALIZED_APPRECIATION < 0 AND YEAR = 2021 AND QUARTER = 4
        ORDER BY UNREALIZED_APPRECIATION ASC;
        """
    },
    {
        "question": "Retrieve the average repurchase rate for repurchase agreements across all funds in Quarter 1 of 2022.",
        "query": """
        SELECT AVG(REPURCHASE_RATE) AS AVG_REPURCHASE_RATE
        FROM REPURCHASE_AGREEMENT
        WHERE YEAR = 2022 AND QUARTER = 1;
        """
    },
    {
        "question": "Find the top 5 issuers by aggregate value of securities on loan in Quarter 3 of 2024.",
        "query": """
        SELECT NAME, AGGREGATE_VALUE
        FROM BORROWER
        WHERE YEAR = 2024 AND QUARTER = 3
        ORDER BY AGGREGATE_VALUE DESC
        LIMIT 5;
        """
    },
    {
        "question": "List the currency codes and their total notional amounts for all foreign currency swaps in Quarter 2 of 2023.",
        "query": """
        SELECT CURRENCY_CODE, SUM(NOTIONAL_AMOUNT) AS TOTAL_NOTIONAL_AMOUNT
        FROM FWD_FOREIGNCUR_CONTRACT_SWAP
        WHERE YEAR = 2023 AND QUARTER = 2
        GROUP BY CURRENCY_CODE;
        """
    },
    {
        "question": "Retrieve all securities lending records where cash collateral value exceeds loan value in Quarter 4 of 2020.",
        "query": """
        SELECT IS_CASH_COLLATERAL, CASH_COLLATERAL_AMOUNT, LOAN_VALUE
        FROM SECURITIES_LENDING
        WHERE CASH_COLLATERAL_AMOUNT > LOAN_VALUE AND YEAR = 2020 AND QUARTER = 4;
        """
    },
    {
        "question": "Find the total liabilities and net assets for each series name, grouped by series, for Quarter 3 of 2021.",
        "query": """
        SELECT SERIES_NAME, SUM(TOTAL_LIABILITIES) AS TOTAL_LIABILITIES, SUM(NET_ASSETS) AS TOTAL_NET_ASSETS
        FROM FUND_REPORTED_INFO
        WHERE YEAR = 2021 AND QUARTER = 3
        GROUP BY SERIES_NAME;
        """
    },
    {
        "question": "Retrieve the issuer names and CUSIP codes for all debt securities with an annualized rate above 5% in Quarter 1 of 2024.",
        "query": """
        SELECT DS.ISSUER_NAME, DS.CUSIP
        FROM DEBT_SECURITY DS
        WHERE DS.ANNUALIZED_RATE > 5 AND DS.YEAR = 2024 AND DS.QUARTER = 1;
        """
    },
    {
        "question": "List the derivative counterparties and their LEIs with unrealized appreciation greater than $1,000,000 in Quarter 2 of 2023.",
        "query": """
        SELECT DC.DERIVATIVE_COUNTERPARTY_NAME, DC.DERIVATIVE_COUNTERPARTY_LEI, SUM(OD.UNREALIZED_APPRECIATION) AS TOTAL_APPRECIATION
        FROM DERIVATIVE_COUNTERPARTY DC
        JOIN OTHER_DERIV OD ON DC.HOLDING_ID = OD.HOLDING_ID
        WHERE OD.UNREALIZED_APPRECIATION > 1000000 AND DC.YEAR = 2023 AND DC.QUARTER = 2
        GROUP BY DC.DERIVATIVE_COUNTERPARTY_NAME, DC.DERIVATIVE_COUNTERPARTY_LEI;
        """
    },
    {
        "question": "Find the total value and count of holdings by issuer type in Quarter 4 of 2022.",
        "query": """
        SELECT ISSUER_TYPE, SUM(CURRENCY_VALUE) AS TOTAL_VALUE, COUNT(*) AS HOLDING_COUNT
        FROM FUND_REPORTED_HOLDING
        WHERE YEAR = 2022 AND QUARTER = 4
        GROUP BY ISSUER_TYPE;
        """
    },
    {
        "question": "Retrieve the name, ticker, and value of the top 10 index components by notional amount in Quarter 3 of 2023.",
        "query": """
        SELECT NAME, TICKER, VALUE
        FROM DESC_REF_INDEX_COMPONENT
        WHERE YEAR = 2023 AND QUARTER = 3
        ORDER BY NOTIONAL_AMOUNT DESC
        LIMIT 10;
        """
    },
    {
        "question": "Find all issuers with holdings marked as restricted securities in Quarter 1 of 2021.",
        "query": """
        SELECT ISSUER_NAME, IS_RESTRICTED_SECURITY
        FROM FUND_REPORTED_HOLDING
        WHERE IS_RESTRICTED_SECURITY = 'Yes' AND YEAR = 2021 AND QUARTER = 1;
        """
    },
    {
        "question": "Retrieve the total principal amounts and their currencies for repurchase collateral in Quarter 2 of 2024.",
        "query": """
        SELECT PRINCIPAL_CURRENCY_CODE, SUM(PRINCIPAL_AMOUNT) AS TOTAL_PRINCIPAL_AMOUNT
        FROM REPURCHASE_COLLATERAL
        WHERE YEAR = 2024 AND QUARTER = 2
        GROUP BY PRINCIPAL_CURRENCY_CODE;
        """
    },
    {
        "question": "List the narrative descriptions of all index baskets reported in Quarter 4 of 2020.",
        "query": """
        SELECT NARRATIVE_DESC
        FROM DESC_REF_INDEX_BASKET
        WHERE YEAR = 2020 AND QUARTER = 4;
        """
    }
]



# initialize chat history and persistent query log
if "messages" not in st.session_state:
    st.session_state.messages = []
if "persistent_query_log" not in st.session_state:
    st.session_state.persistent_query_log = []

# function to execute SQL query w debugging
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
    You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. 
    Use the provided database schema and the following examples as a reference to ensure accurate queries. 

    Examples:
    {example_prompts_and_queries}

    Schema Details:
    {schema_to_string(schema)}

    Rules:
    1. Only use `QUARTER` and `YEAR` in the SQL query. Do not use any specific dates. Use the `QUARTER` and `YEAR` columns directly, and do not use any functions like QUARTER() or YEAR().
    2. Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
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














# import os
# import sqlite3
# import pandas as pd
# import streamlit as st
# import openai
# from dotenv import load_dotenv
# from pathlib import Path
# from api_connection import openai_message_creator, query_openai, schema_to_string, process_prompt_for_quarter_year
# from data_loading import load_schema

# # load env variables
# load_dotenv()
# API_KEY = os.getenv("OPENAI_API_KEY")
# openai.api_key = API_KEY

# # db path
# db_path = Path("data/sec_nport_data_subset.db")

# # Load the schema
# schema_file_path = "Table_Schema.txt"
# schema = load_schema(schema_file_path)

# # app title
# st.title("PIMCO Bot")

# # initialize chat history and persistent query log
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "persistent_query_log" not in st.session_state:
#     st.session_state.persistent_query_log = []

# # function to execute SQL query w debugging
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

# # function to validate SQL query
# def validate_sql_query(query):
#     """
#     Validates that the SQL query is well-formed and safe to execute.
#     """
#     # Basic validation to check for SELECT and FROM statements
#     if "SELECT" in query and "FROM" in query and ";" in query:
#         return True
#     return False

# # display persistent query log
# if "persistent_query_log" in st.session_state and st.session_state.persistent_query_log:
#     for query_record in st.session_state.persistent_query_log:
#         st.write("#### Question")
#         st.markdown(query_record["question"])
#         st.write("#### SQL Query")
#         st.code(query_record["query"], language="sql")
#         st.write("#### Explanation")
#         st.markdown(query_record["explanation"])
#         st.write("#### Results")
#         st.dataframe(query_record["results"])

# # user input
# if prompt := st.chat_input("Enter your question about the database:"):
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt})
    
#     # Process specific dates or date ranges in the prompt
#     refined_prompt = process_prompt_for_quarter_year(prompt)
#     refined_prompt = f"Generate an SQL query for this request: '{refined_prompt}'. Return only the query and an explanation."

#     # Generate OpenAI messages with schema
#     system_message_string = f"""
#     You are an assistant that generates SQL queries based on user questions related to the N-PORT dataset. 
#     Use the provided database schema to ensure accurate queries. Respond in the following format:
#     SQL Query:
#     [Generated SQL Query]

#     Explanation:
#     [Explanation of the Query]

#     Rules:
#     1. Only use `QUARTER` and `YEAR` in the SQL query. Do not use any specific dates. Use the `QUARTER` and `YEAR` columns directly, and do not use any functions like QUARTER() or YEAR().
#     2. Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
#     """
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
#                 # Save query, explanation, and results to persistent query log
#                 query_record = {
#                     "question": prompt,
#                     "query": cleaned_sql_query,
#                     "explanation": explanation,
#                     "results": df_result
#                 }
#                 st.session_state.persistent_query_log.append(query_record)

#                 # Display SQL query, explanation, and results
#                 st.write("#### Question")
#                 st.markdown(query_record["question"])
#                 st.write("#### SQL Query")
#                 st.code(query_record["query"], language="sql")
#                 st.write("#### Explanation")
#                 st.markdown(query_record["explanation"])
#                 st.write("#### Results")
#                 st.dataframe(query_record["results"])
#             else:
#                 st.error("Failed to execute the query. Check the logs for details.")
#         else:
#             # If the query is invalid, show an error message
#             st.error("Invalid SQL query generated. Please review.")
#     else:
#         st.error("No response generated. Please try again.")


