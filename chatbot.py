import os
import sqlite3
import pandas as pd
import streamlit as st
import openai
import io
from dotenv import load_dotenv
from pathlib import Path
from api_connection import openai_message_creator, query_openai, schema_to_string, process_prompt_for_quarter_year
from schema_loader import load_schema
from pydantic import BaseModel, Field
from typing import List, Union

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
            Let's think step by step. The SQL query for the question "What are the cash holdings of the Vanguard Total Bond Market Index Fund as of the latest reporting date?" needs these tables = [FUND_REPORTED_HOLDING, FUND_REPORTED_INFO, SUBMISSION], so we need JOIN.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM".
            """,
            "schema_links": "FUND_REPORTED_INFO.ACCESSION_NUMBER = FUND_REPORTED_HOLDING.ACCESSION_NUMBER, SUBMISSION.ACCESSION_NUMBER = fri.ACCESSION_NUMBER, FUND_REPORTED_HOLDING.BALANCE, FUND_REPORTED_INFO.SERIES_NAME, SUBMISSION.REPORT_DATE, Vanguard Total Bond Market Index Fund"
        },
        {
            "question": "What is the percentage allocation to derivatives for all funds in Q1 2020?",
            "query": """
            SELECT
                fri.SERIES_NAME,
                (SUM(dric.NOTIONAL_AMOUNT) / fri.TOTAL_ASSETS) * 100 AS PercentageAllocationToDerivatives
            FROM FUND_REPORTED_INFO fri
            JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
            JOIN DESC_REF_INDEX_COMPONENT dric ON frh.HOLDING_ID = dric.HOLDING_ID
            WHERE fri.QUARTER = 1 AND fri.YEAR = 2020
            GROUP BY fri.SERIES_NAME, fri.TOTAL_ASSETS;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "What is the percentage allocation to derivatives for all funds in Q1 2020?" needs these tables = [FUND_REPORTED_INFO, FUND_REPORTED_HOLDING, DESC_REF_INDEX_COMPONENT], so we need JOINs on ACCESSION_NUMBER and HOLDING_ID.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM".
            """,
            "schema_links": "FUND_REPORTED_INFO.ACCESSION_NUMBER = FUND_REPORTED_HOLDING.ACCESSION_NUMBER, FUND_REPORTED_HOLDING.HOLDING_ID = DESC_REF_INDEX_COMPONENT.HOLDING_ID, FUND_REPORTED_INFO.SERIES_NAME, DESC_REF_INDEX_COMPONENT.NOTIONAL_AMOUNT, FUND_REPORTED_INFO.TOTAL_ASSETS, FUND_REPORTED_INFO.QUARTER, FUND_REPORTED_INFO.YEAR, 1, 2020"
        },
        {
            "question": "What is the cash collateral value for holdings involved in securities lending in Q1 2020?",
            "query": """
            SELECT rc.HOLDING_ID, rc.COLLATERAL_AMOUNT
            FROM SECURITIES_LENDING sl
            JOIN REPURCHASE_COLLATERAL rc ON sl.HOLDING_ID = rc.HOLDING_ID
            WHERE sl.IS_CASH_COLLATERAL = 'Y' AND sl.YEAR = 2020 AND sl.QUARTER = 1;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "What is the cash collateral value for holdings involved in securities lending in Q1 2020?" needs these tables = [SECURITIES_LENDING, REPURCHASE_COLLATERAL], so we need JOIN on HOLDING_ID.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM".
            """,
            "schema_links": "SECURITIES_LENDING.HOLDING_ID = REPURCHASE_COLLATERAL.HOLDING_ID, SECURITIES_LENDING.IS_CASH_COLLATERAL, REPURCHASE_COLLATERAL.COLLATERAL_AMOUNT, SECURITIES_LENDING.YEAR, SECURITIES_LENDING.QUARTER, Y, 2020, 1"
        },
        {
            "question": "Compare unrealized appreciation for PIMCO and Vanguard funds in Q3 2023.",
            "query": """
            SELECT fri.SERIES_NAME, SUM(fri.NET_UNREALIZE_AP_NONDERIV_MON1 + fri.NET_UNREALIZE_AP_NONDERIV_MON2 + fri.NET_UNREALIZE_AP_NONDERIV_MON3) AS TotalAppreciation
            FROM FUND_REPORTED_INFO fri
            JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
            JOIN FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc ON frh.HOLDING_ID = ffnc.HOLDING_ID
            WHERE fri.SERIES_NAME LIKE '%PIMCO%' OR fri.SERIES_NAME LIKE '%Vanguard%' AND fri.YEAR = 2023 AND fri.QUARTER = 3
            GROUP BY fri.SERIES_NAME;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Compare unrealized appreciation for PIMCO and Vanguard funds in Q3 2023" needs these tables = [FUND_REPORTED_INFO, FUND_REPORTED_HOLDING, FUT_FWD_NONFOREIGNCUR_CONTRACT], so we need JOINs on ACCESSION_NUMBER and HOLDING_ID.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM".
            """,
            "schema_links": "FUT_FWD_NONFOREIGNCUR_CONTRACT.HOLDING_ID = FUND_REPORTED_HOLDING.HOLDING_ID, FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.NET_UNREALIZE_AP_NONDERIV_MON1, FUND_REPORTED_INFO.NET_UNREALIZE_AP_NONDERIV_MON2, FUND_REPORTED_INFO.NET_UNREALIZE_AP_NONDERIV_MON3, FUND_REPORTED_HOLDING.HOLDING_ID, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, PIMCO, Vanguard, 2023, 3"
        },
        {
            "question": "Find the top 5 issuers by cumulative notional amount of derivatives in 2019.",
            "query": """
            SELECT frh.ISSUER_NAME, SUM(ffnc.NOTIONAL_AMOUNT) AS TotalNotional
            FROM FUND_REPORTED_HOLDING frh
            JOIN FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc ON frh.HOLDING_ID = ffnc.HOLDING_ID
            WHERE ffnc.YEAR = 2019
            GROUP BY frh.ISSUER_NAME
            ORDER BY TotalNotional DESC
            LIMIT 5;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Find the top 5 issuers by cumulative notional amount of derivatives in 2019" needs these tables = [FUND_REPORTED_HOLDING, FUT_FWD_NONFOREIGNCUR_CONTRACT], so we need JOIN.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM".
            """,
            "schema_links": "FUND_REPORTED_HOLDING.ISSUER_NAME, FUT_FWD_NONFOREIGNCUR_CONTRACT.NOTIONAL_AMOUNT, FUT_FWD_NONFOREIGNCUR_CONTRACT.YEAR, FUND_REPORTED_HOLDING.HOLDING_ID = FUT_FWD_NONFOREIGNCUR_CONTRACT.HOLDING_ID, 2019"
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
            Let's think step by step. The SQL query for the question "Compare derivative allocation trends for Fidelity funds from 2020 to 2023" needs these tables = [FUND_REPORTED_INFO, FUND_REPORTED_HOLDING, FUT_FWD_NONFOREIGNCUR_CONTRACT], so we need JOINs on ACCESSION_NUMBER and HOLDING_ID.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
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
            Let's think step by step. The SQL query for the question "What is the currency-wise allocation of restricted securities in Q1 2023?" needs these tables = [FUND_REPORTED_HOLDING, FUND_REPORTED_INFO], so we need JOIN on ACCESSION_NUMBER.
            Plus, it doesn't require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer to the questions = [""].
            So, we need JOIN and don't need nested queries, then the SQL query can be classified as "MEDIUM."
            """,
            "schema_links": "FUND_REPORTED_HOLDING.CURRENCY_CODE, FUND_REPORTED_HOLDING.CURRENCY_VALUE, FUND_REPORTED_HOLDING.IS_RESTRICTED_SECURITY, FUND_REPORTED_INFO.TOTAL_ASSETS, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, FUND_REPORTED_HOLDING.ACCESSION_NUMBER = FUND_REPORTED_INFO.ACCESSION_NUMBER, Y, 2023, 1"
        }
    ],
    "hard": [
        {
            "question": "Find the top 3 issuers with the highest notional amounts in derivative contracts for Q3 2023.",
            "query": """
            SELECT frh.ISSUER_NAME, frh.YEAR, frh.QUARTER, TotalNotional
            FROM (
                SELECT ffnc.HOLDING_ID, SUM(ffnc.NOTIONAL_AMOUNT) AS TotalNotional
                FROM FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc
                WHERE YEAR = 2020 AND QUARTER = 1
                GROUP BY ffnc.HOLDING_ID
            ) AS IssuerNotional
            JOIN FUND_REPORTED_HOLDING frh ON frh.HOLDING_ID = IssuerNotional.HOLDING_ID
            ORDER BY IssuerNotional.TotalNotional DESC
            LIMIT 3;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Find the top 3 issuers with the highest notional amounts in derivative contracts for Q3 2023" needs these tables = [FUT_FWD_NONFOREIGNCUR_CONTRACT].
            Plus, it requires nested queries to answer the questions = ["What is the total notional amount for each issuer in Q3 2023?"].
            So, we don't need JOINs but do need nested queries, then the SQL query can be classified as "HARD".
            """,
            "schema_links": "FUT_FWD_NONFOREIGNCUR_CONTRACT.ISSUER_NAME, FUT_FWD_NONFOREIGNCUR_CONTRACT.NOTIONAL_AMOUNT, FUT_FWD_NONFOREIGNCUR_CONTRACT.YEAR, FUT_FWD_NONFOREIGNCUR_CONTRACT.QUARTER"
        },
        {
            "question": "Which funds reported the highest net realized gains among the top 10 funds by total assets in Q3 2023?",
            "query": """
            SELECT SERIES_NAME,
                (NET_REALIZE_GAIN_NONDERIV_MON1 + NET_REALIZE_GAIN_NONDERIV_MON2 + NET_REALIZE_GAIN_NONDERIV_MON3) AS TotalRealizedGain
            FROM FUND_REPORTED_INFO
            WHERE SERIES_NAME IN (
                SELECT SERIES_NAME
                FROM (
                    SELECT SERIES_NAME, TOTAL_ASSETS
                    FROM FUND_REPORTED_INFO
                    WHERE YEAR = 2023 AND QUARTER = 3
                    ORDER BY TOTAL_ASSETS DESC
                    LIMIT 10
                ) AS TopFunds
            )
            ORDER BY TotalRealizedGain DESC;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Which funds reported the highest net realized gains among the top 10 funds by total assets in Q3 2023?" needs this table = [FUND_REPORTED_INFO], so we don't need JOINs.
            Plus, it requires nested queries with IN and FROM, and we need the answer to the questions = ["Which are the top 10 funds by total assets in Q3 2023?"].
            So, we don't need JOINs but need nested queries, then the SQL query can be classified as "HARD". 
            """,
            "schema_links": "FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.TOTAL_ASSETS, FUND_REPORTED_INFO.NET_REALIZE_GAIN_NONDERIV_MON1, FUND_REPORTED_INFO.NET_REALIZE_GAIN_NONDERIV_MON2, FUND_REPORTED_INFO.NET_REALIZE_GAIN_NONDERIV_MON3, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, 2023, 3"
        },
        {
            "question": "Find the net realized gain for the largest funds by liabilities in each quarter of 2023.",
            "query": """
            SELECT SERIES_NAME, QUARTER, NET_REALIZE_GAIN_NONDERIV_MON1 + NET_REALIZE_GAIN_NONDERIV_MON2 + NET_REALIZE_GAIN_NONDERIV_MON3 AS TotalRealizedGain
            FROM FUND_REPORTED_INFO
            WHERE SERIES_NAME IN (
                SELECT SERIES_NAME
                FROM (
                    SELECT SERIES_NAME, TOTAL_LIABILITIES
                    FROM FUND_REPORTED_INFO
                    WHERE YEAR = 2023
                    ORDER BY TOTAL_LIABILITIES DESC
                    LIMIT 5
                ) AS TopLiabilityFunds
            )
            ORDER BY QUARTER;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Find the net realized gain for the largest funds by liabilities in each quarter of 2023" needs this table = [FUND_REPORTED_INFO], so we don't need JOINs.
            Plus, it requires nested queries with IN, and we need the answer to the questions = ["Which are the top funds by total liabilities in 2023?"].
            So, we don't need JOINs but need nested queries, then the SQL query can be classified as "HARD". 
            """,
            "schema_links": "FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.TOTAL_LIABILITIES, FUND_REPORTED_INFO.QUARTER, FUND_REPORTED_INFO.NET_REALIZE_GAIN_NONDERIV_MON1, FUND_REPORTED_INFO.NET_REALIZE_GAIN_NONDERIV_MON2, FUND_REPORTED_INFO.NET_REALIZE_GAIN_NONDERIV_MON3, FUND_REPORTED_INFO.YEAR, 2023"
        }
    ]
}

# initialize chat history and persistent query log
if "messages" not in st.session_state:
    st.session_state.messages = []
if "persistent_query_log" not in st.session_state:
    st.session_state.persistent_query_log = []


# Methodology: Chain of Thought Reasoning Schema with Pydantic
class Background(BaseModel):
    """A setup to the background for the user."""
    background: str = Field(description="Background for the user's question", min_length=10)

class Thought(BaseModel):
    """A thought about the user's question."""
    thought: str = Field(description="Text of the thought.")
    helpful: bool = Field(description="Whether the thought is helpful to solving the user's question.")

class Observation(BaseModel):
    """An observation on the sequence of thoughts and observations generated so far."""
    observation: str = Field(description="An insightful observation on the sequence of thoughts and observations generated so far.")
    
class Reasonings(BaseModel):
    """Returns a detailed reasoning to the user's question."""
    reasonings: List[Union[Background, Thought, Observation]] = Field(description="Reasonings to solve the users questions.")

class FinalQueryOutput(BaseModel):
    user_nlp_query: str = Field(description="Returns the exact question that the user asked in natural language.")
    reasonings: List[Union[Background, Thought, Observation]] = Field(description="Reasonings to solve the users questions.")
    generated_sql_query: str = Field(description="Returns the SQL Language Query corresponding to the NLP description of the user question.")


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
            - Hard Questions: {[example for example in example_prompts_and_queries['hard']]}
        3. Analyze Query Requirements:
        - Original Question: Consider what information the query is supposed to retrieve.
        - Executed SQL Query: Review the SQL query that was previously executed and led to an error or incorrect result.
        - Execution Result: Analyze the outcome of the executed query to identify why it failed (e.g., syntax errors, incorrect column references, logical mistakes).
        4. Adhere to Rules:
        - Remember the rules you must follow:
            - Only use `QUARTER` and `YEAR` in the SQL query, do not use any specific dates. If the user question contains a specific date, please convert this to the appropriate year and quarter.
            - Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
            - All queries must be valid to access a SQLite database (e.g., use the command LIMIT instead of FETCH)
            - When you start the Explanation you must put “Explanation:” before it
            - Use "Y" and "N" instead of "YES" and "NO" in the SQL query (e.g., WHERE IS_DEFAULT = 'Y' instead of WHERE IS_DEFAULT = 'YES').
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
    You are an assistant that generates SQL queries and their explanations based on user questions related to the SEC N-PORT dataset. 

    **Background:**
    N-PORT filings contain detailed reports submitted by registered investment companies, including mutual funds and exchange-traded funds (ETFs), which disclose their portfolio holdings on a monthly basis. 
    These filings provide transparency into the asset composition, performance, and risk exposures of these funds, offering valuable insights for investors, regulators, and researchers.
    Your goal is to write, explain, and execute SQL queries on a SQLite database to answer natural language questions asked by the user. 

    **Procedure**
    1. Review Database Schema
    - Examine the following schema details to understand the database structure:
    {schema_to_string(schema)}
    2. Review Example User Questions, Queries, and Explanations
    - Examine the following examples as a reference to guide your response:
        - Easy Questions: {[example for example in example_prompts_and_queries['easy']]}
        - Medium Questions: {[example for example in example_prompts_and_queries['medium']]}
    3. Chain of Thought Reasoning:
    - For each question, break down the reasoning steps to explain why the SQL query works. Each reasoning should progressively increase in complexity.
    - Explain why nested queries or JOINs are or are not required.
    - If any aggregation or grouping is required, explain why.
    - Provide insights into how the structure of the SQL query answers the user's question.
    4. Stucture Reasoning:
    - The explanation of the SQL query should be structured as follows:
        - Background: (Setup the background for the question)
        - Thoughts: (Explain thoughts progressively and logically)
        - Observation: (Final observation or conclusion)
    
    **Output Format:**
    [SQL Query]
    Explanation: [Explanation of SQL Query]

    **Rules:**
    1. Only use `QUARTER` and `YEAR` in the SQL query, do not use any specific dates. If the user question contains a specific date, please convert this to the appropriate year and quarter.
    2. Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
    3. All queries must be valid to access a SQLite database (e.g., use the command LIMIT instead of FETCH)
    4. When you start the Explanation you must put “Explanation:” before it
    5. Use "Y" and "N" instead of "YES" and "NO" in the SQL query (e.g., WHERE IS_DEFAULT = 'Y' instead of WHERE IS_DEFAULT = 'YES').
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

                # Convert the DataFrame to CSV format
                csv = df_result.to_csv(index=False)

                # Create a downloadable CSV file 
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
            else:
                st.error("Failed to execute the query. Check the logs for details.")
        else:
            # If the query is invalid, show an error message
            st.error("Invalid SQL query generated. Please review.")
    else:
        st.error("No response generated. Please try again.")







# {
#             "question": " ",
#             "query": """
            
#             """,
#             "reasoning": """
            
#             """,
#             "schema_links": " "
#         }
