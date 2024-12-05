import os
import sqlite3
import pandas as pd
import openai
import json
import textwrap
from dotenv import load_dotenv
from pathlib import Path
from api_connection import (
    openai_message_creator,
    query_openai,
    schema_to_string,
    process_prompt_for_quarter_year
)
from schema_loader import load_schema
from pydantic import BaseModel, Field
from typing import List, Union, Optional, Tuple

__all__ = [
    "execute_sql_query",
    "validate_sql_query",
    "process_prompt_for_quarter_year",
    "query_openai",
    "openai_message_creator",
    "generate_system_message",
    "schema",
    "example_prompts_and_queries"
]

# Load Environment Variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

# Database Path
db_path = Path("data/sec_nport_data_combined.db")

# Load the Schema
schema_file_path = "data/data_schema2.txt"
schema = load_schema(schema_file_path)
key_schema_file_path = "data/key_schema.txt"
key_schema = load_schema(key_schema_file_path)


# Pydantic Models
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
    reasonings: list[Union[Background, Thought, Observation]] = Field(
        description="Reasonings to solve the users questions."
    )

sample_reasonings = Reasonings(reasonings=[
    Background(background="The task is to generate SQL from natural language query."),
    Thought(thought="First thought", helpful=True),
    Thought(thought="Second thought", helpful=True),
    Thought(thought="Third thought", helpful=True),
    Thought(thought="Fourth thought", helpful=True),
    Thought(thought="Fifth thought", helpful=True),
    Observation(observation="Astute observation")
])

sample_reasonings.json()

reasonings_schema_json = Reasonings.schema_json()

class FinalQueryOutput(BaseModel):
    user_nlp_query: str = Field(
        description=f"""Returns the exact question that the user asked in natural language
        which is to be translated into SQL Query."""
    )
    reasonings: list[Union[Background, Thought, Observation]] = Field(
        description="Reasonings to solve the users questions."
    )
    generated_sql_query: str = Field(
        description=f"""Returns the SQL Language Query corresponding to the
        NLP description of the user question."""
    )

final_output_schema_json = FinalQueryOutput.schema_json()

sample_output = FinalQueryOutput(
    user_nlp_query="Get count of rows.",
    reasonings=[
        Background(background="Deadline is near"),
        Thought(thought="First thought", helpful=True),
        Thought(thought="Second thought", helpful=True),
        Thought(thought="Third thought", helpful=True),
        Thought(thought="Fourth thought", helpful=True),
        Thought(thought="Fifth thought", helpful=True),
        Observation(observation="Astute observation")
    ],
    generated_sql_query="SELECT COUNT(*) FROM fact_table"
)

sample_output.json()

# System Prompts
system_prompt_snippet_001 = """
You are the most intelligent person in the world.
"""
system_prompt_snippet_002 = """
You will receive a $500 tip if you follow ALL the instructions specified.
"""
system_prompt_snippet_003 = """
Use step by step reasoning and at each step generate thoughts of increasing complexity.
"""
system_prompt_snippet_004 = """
Getting this answer right is important for my career. Please do your best.
"""
system_prompt = f"""
{system_prompt_snippet_001}
{system_prompt_snippet_002}
{system_prompt_snippet_003}
{system_prompt_snippet_004}
"""

def generate_system_message() -> str:
    """
    Generates the system message by combining predefined snippets.
    """
    return system_prompt


# Example Prompts and Queries
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
        },
        {
            "question": "Which funds hold restricted securities and have total assets greater than the average total assets of all funds in Q4 2023?",
            "query": """
            SELECT DISTINCT fri.SERIES_NAME, fri.TOTAL_ASSETS
            FROM FUND_REPORTED_INFO fri
            JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
            WHERE frh.IS_RESTRICTED_SECURITY = 'Y'
                AND fri.TOTAL_ASSETS > (
                    SELECT AVG(TOTAL_ASSETS)
                    FROM FUND_REPORTED_INFO
                    WHERE YEAR = 2023 AND QUARTER = 4
                )
                AND fri.YEAR = 2023 AND fri.QUARTER = 4;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Which funds hold restricted securities and have total assets greater than the average total assets of all funds in Q4 2023?" needs these tables = [FUND_REPORTED_INFO, FUND_REPORTED_HOLDING], so we need JOIN.
            Plus, it requires nested queries with AVG, and we need the answer to the questions = ["What is the average total assets of all funds in Q4 2023?"].
            So, we need JOIN and need nested queries, then the SQL query can be classified as "HARD".
            """,
            "schema_links": "FUND_REPORTED_INFO.ACCESSION_NUMBER = FUND_REPORTED_HOLDING.ACCESSION_NUMBER, FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.TOTAL_ASSETS, FUND_REPORTED_HOLDING.IS_RESTRICTED_SECURITY, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, Y, 2023, 4"
        },
        {
            "question": "Find the quarterly change in net assets for funds with the largest liabilities-to-assets ratio in 2023.",
            "query": """
            SELECT SERIES_NAME, QUARTER,
                NET_ASSETS - LAG(NET_ASSETS) OVER (PARTITION BY SERIES_NAME ORDER BY QUARTER) AS NetAssetChange
            FROM FUND_REPORTED_INFO
            WHERE SERIES_NAME IN (
                SELECT SERIES_NAME
                FROM (
                    SELECT SERIES_NAME, (TOTAL_LIABILITIES / TOTAL_ASSETS) AS LiabilityToAssetRatio
                    FROM FUND_REPORTED_INFO
                    WHERE YEAR = 2023
                    ORDER BY LiabilityToAssetRatio DESC
                    LIMIT 5
                ) AS TopRatioFunds
            )
            ORDER BY QUARTER;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Find the quarterly change in net assets for funds with the largest liabilities-to-assets ratio in 2023?" needs these tables = [FUND_REPORTED_INFO], so we need JOIN.
            Plus, it requires nested queries with (ORDER BY, LIMIT), and we need the answer to the questions = [“What are the top 5 funds by liabilities-to-assets ratio in 2023?”].
            So, we need JOIN and need nested queries, then the SQL query can be classified as "HARD".
            """,
            "schema_links": "FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.NET_ASSETS, FUND_REPORTED_INFO.QUARTER, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.TOTAL_LIABILITIES, FUND_REPORTED_INFO.TOTAL_ASSETS, 2023"
        },
        {
            "question": "List the funds with cash holdings greater than the average cash holdings in Q2 2023.",
            "query": """
            SELECT SERIES_NAME
            FROM FUND_REPORTED_INFO
            WHERE CASH_NOT_RPTD_IN_C_OR_D > (
                SELECT AVG(CASH_NOT_RPTD_IN_C_OR_D)
                FROM FUND_REPORTED_INFO
                WHERE YEAR = 2023 AND QUARTER = 2
            )
            AND YEAR = 2023 AND QUARTER = 2;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "List the funds with cash holdings greater than the average cash holdings in Q2 2023" needs this table = [FUND_REPORTED_INFO], so we don't need JOINs.
            Plus, it requires a nested query with AVG, and we need the answer to the question = ["What is the average cash holdings for all funds in Q2 2023?"].
            So, we don't need JOINs but need a nested query, then the SQL query can be classified as "HARD."
            """,
            "schema_links": "FUND_REPORTED_INFO.CASH_NOT_RPTD_IN_C_OR_D, FUND_REPORTED_INFO.SERIES_NAME, FUND_REPORTED_INFO.YEAR, FUND_REPORTED_INFO.QUARTER, 2023, 2"
        },
        {
            "question": "Which funds have derivatives with a counterparty LEI matching a repurchase counterparty's LEI, and the total unrealized appreciation for those derivatives exceeds $1 million in Q2 2024?",
            "query": """
            SELECT fri.SERIES_NAME, SUM(swd.UNREALIZED_APPRECIATION) AS TotalAppreciation, swd.YEAR, swd.QUARTER
            FROM FUND_REPORTED_INFO fri
            JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
            JOIN SWAPTION_OPTION_WARNT_DERIV swd ON frh.HOLDING_ID = swd.HOLDING_ID
            JOIN (
                SELECT rc.LEI
                FROM REPURCHASE_COUNTERPARTY rc
            ) rep ON swd.HOLDING_ID = frh.HOLDING_ID
            WHERE swd.UNREALIZED_APPRECIATION > 1000000 AND swd.YEAR = 2024 AND swd.QUARTER = 2
            GROUP BY fri.SERIES_NAME;
            """,
            "reasoning": """
            Let's think step by step. The SQL query for the question "Which funds have derivatives with a counterparty LEI matching a repurchase counterparty's LEI, and the total unrealized appreciation for those derivatives exceeds $1 million in Q2 2024?" needs these tables = [FUND_REPORTED_INFO, FUND_REPORTED_HOLDING, SWAPTION_OPTION_WARNT_DERIV, REPURCHASE_COUNTERPARTY], so we need JOIN.
            Plus, it requires nested queries with (IN, JOIN), and we need the answer to the questions = [“What are the LEIs of repurchase counterparties?”].
            So, we need JOIN and nested queries, then the SQL query can be classified as "HARD".
            """,
            "schema_links": "FUND_REPORTED_INFO.ACCESSION_NUMBER = FUND_REPORTED_HOLDING.ACCESSION_NUMBER, FUND_REPORTED_HOLDING.HOLDING_ID = SWAPTION_OPTION_WARNT_DERIV.HOLDING_ID, SWAPTION_OPTION_WARNT_DERIV.UNREALIZED_APPRECIATION, REPURCHASE_COUNTERPARTY.LEI, SWAPTION_OPTION_WARNT_DERIV.YEAR, SWAPTION_OPTION_WARNT_DERIV.QUARTER, 1000000, 2024, 2"
        }
    ]
}

# User Prompt Generation
def get_user_prompt_for_question(input_question: str) -> str:
    """
    Generates the complete user prompt for OpenAI based on the current schema and examples.
    """
    complete_user_prompts = textwrap.dedent(f"""
    **Task Description**
    You are an assistant that generates SQL queries and their reasonings based on user questions related to the SEC N-PORT dataset. 

    **N-PORT Dataset Overview**
    N-PORT filings contain detailed reports submitted by registered investment companies, including mutual funds and exchange-traded funds (ETFs), which disclose their portfolio holdings on a monthly basis. 
    These filings provide transparency into the asset composition, performance, and risk exposures of these funds, offering valuable insights for investors, regulators, and researchers.

    Your goal is to write, explain, and execute SQL queries on a SQLite database to answer natural language questions asked by the user. 

    **Database Schema Description**
    Examine the following schema details to understand the database structure:
    {schema}
    
    Examine the following key schema that identifies the primary keys for each table in the database:
    {key_schema}

    **Example Natural Language Questions and Their Corresponding SQL Queries and Reasonings**
    Examine the following examples as a reference to guide your response:
    - Easy Questions: {[example for example in example_prompts_and_queries['easy']]}
    - Medium Questions: {[example for example in example_prompts_and_queries['medium']]}
    - Hard Questions: {[example for example in example_prompts_and_queries['hard']]}

    **Rules for SQL Query Generation**
    - Only use `QUARTER` and `YEAR` in the SQL query, do not use any specific dates. If the user question contains a specific date, please convert this to the appropriate year and quarter.
    - Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
    - All queries must be valid to access a SQLite database (e.g., use the command LIMIT instead of FETCH)
    - Use "Y" and "N" instead of "YES" and "NO" in the SQL query (e.g., WHERE IS_DEFAULT = 'Y' instead of WHERE IS_DEFAULT = 'YES').
    - Use the key schema to identify the primary keys for each table in the database. If you need to join two tables that do not have the same primary key, find an intermidiate table that has both primary keys.
    """)

    user_prompt = textwrap.dedent(f"""
    Here's the question that the user entered:
    {input_question}

    Generate a SQL query corresponding to the given input question and the description of the table provided below.
    {complete_user_prompts}

    Reasoning as to why the query is correct:
    {reasoning_instructions}
    {reasoning_schema_instructions}

    Response for SQL Generation:
    """)
    
    return user_prompt


# Reasoning Instructions
reasoning_instructions = """
1. Reasoning you provide should first focus on why a nested query was chosen or why it wasn't chosen.
2. It should give a query plan on how to solve this question - explain 
the mapping of the columns to the words in the input question.
3. It should explain each of the clauses and why they are structured the way they are structured. 
For example, if there is a `group_by`, an explanation should be given as to why it exists.
4. If there's any sum() or any other function used it should be explained as to why it was required.

Format the generated sql with proper indentation - the columns in the (`select` statement should have more indentation than keyword `select` and so on for each SQL clause.)
"""  

# Thought Instructions
thought_instructions = f"""

Thought Instructions:

Generate thoughts of increasing complexity.
Each thought should build on the previous ones and thoughts should progressively cover the nuances of the problem at hand.

First set of thoughts should be on whether a the query requires Common Table Expressions (CTEs) to calculate the results for sub queries. 
- Prefer using Common Table Expressions rather than case when statements or nested subqueries.
- If CTEs are required then for each CTE, an analysis of the purpose of each CTE should be done.
- An overall structure should be outlined as to what will be calculated in each CTE.

Next set of thoughts should be on deciding the relevant tables that should be used for the query.
- For each table, one set of thoughts should be to summarize their primary and secondary keys.
- A list of columns that should be extracted from them should be mentioned.
- This list should be checked against the list of columns present in the table which is mentioned in the schema description provided earlier.

Next set of thoughts should be to figure out the joins that need to be usedin the query.
- A justification for using left, right or inner join should be provided.

Next set of thoughts should be on extracting out the names of as many of the relevant columns as possible for all CTEs and for all the sql clauses such as the 
`select`, `where` and `group_by` clauses.
- There might be additions or deletions from this list based on the following additional thoughts to be generated.

Generate a thought to figure out the possible phrases in the query which can be used as values of the columns present in the table so as to use them in the `where` clause.

Generate a thought to compare these extracted values with the list of possible values of columns listed in the information for the columns so as to use the exact string in the `where` clause.

The above thoughts about 
    1. phrases for values of columns
    2. query phrase to column value mapping
    3. Group by column
should be generated for each of the CTE separately.

If the input question is similar to any of the examples given above, then a thought should be generated to detect that and then that example should be followed closely to get the SQL for the input question given.

Closing Thoughts and Observations
    These should summarize:
    1. The structure of the SQL query:
        - This states whether the query has any nested query.
        If so, the structure of the nested query is also mentioned.
        If not, a summary of the function of each of the select`, `where`, `group_by` etc. clauses should be mentioned.
    2. An explanation of how the query solves the user question.
"""


reasoning_schema_instructions = f"""
Use the following JSON Schema as the grammar to create the structure for the step by step reasoning, and then to create the final SQL query.

Schema for Reasoning:
{reasonings_schema_json}

The instructions on how to structure the reasoning is provided below:
{thought_instructions}

Schema for Overall Output: (This includes the reasonings schema above as an element)
{final_output_schema_json}

The final response should be a json with `names` as `user_nlp_query`, `reasonings`, and `generated_sql_query`:
1. `user_nlp_query` should be exactly the same as the user query in string format.
2. `reasonings` should provide the reasoning steps adhering to the Reasonings schema.
3. `generated_sql_schema` should provide the SQL query generated in string format.
- this is the final answer.
"""

def execute_sql_query(query: str, db_path: Path) -> Optional[pd.DataFrame]:
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
        query_fixing_prompt = textwrap.dedent(f"""
        **Task Description:**
        You are an SQL database expert tasked with correcting a SQL query. A previous attempt to run a query did not yield the correct results,
        either due to errors in execution or because the result returned was empty or unexpected. Your role is to analyze the error based on 
        the provided database schema and the details of the failed execution, and then provide a corrected version of the SQL query. 

        **Procedure:**
        1. Review Database Schema
        - Examine the following schema details to understand the database structure:
        {schema}
        - Examine the following key schema that identifies the primary keys for each table in the database:
        {key_schema}
        2. Review Example User Questions, Queries, and Reasonings
        - Examine the following examples as a reference to guide your corrected response:
            - Easy Questions: {[example for example in example_prompts_and_queries['easy']]}
            - Medium Questions: {[example for example in example_prompts_and_queries['medium']]}
            - Hard Questions: {[example for example in example_prompts_and_queries['hard']]}
        3. Analyze Query Requirements:
        - Original Question: Consider what information the query is supposed to retrieve.
            - Here's the question that the user entered: {input_question}
        - Executed SQL Query: Review the SQL query that was previously executed and led to an error or incorrect result.
        - Execution Result: Analyze the outcome of the executed query to identify why it failed (e.g., syntax errors, incorrect column references, logical mistakes).
        4. Review Reasoning Instructions:
        {reasoning_instructions}
        {reasoning_schema_instructions}
        5. Adhere to Rules:
        - Remember the rules you must follow:
            - Only use `QUARTER` and `YEAR` in the SQL query, do not use any specific dates. If the user question contains a specific date, please convert this to the appropriate year and quarter.
            - Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
            - All queries must be valid to access a SQLite database (e.g., use the command LIMIT instead of FETCH)
            - Use "Y" and "N" instead of "YES" and "NO" in the SQL query (e.g., WHERE IS_DEFAULT = 'Y' instead of WHERE IS_DEFAULT = 'YES').
            - Use the key schema to identify the primary keys for each table in the database. If you need to join two tables that do not have the same primary key, find an intermidiate table that has both primary keys.
        6. Correct the Query and Corresponding Reasoning:
        - Modify the SQL query to address the identified issues, ensuring it correctly fetches the requested data according to the database schema and query requirements.

        **Schema for Output:**
        - This can be found in the {reasoning_schema_instructions}

        Based on the question, table schema, and previous query, analyze the result to fix the query and make it valid and executable.
        """)

        # Query OpenAI to fix the query
        fixing_response = query_openai(openai_message_creator(
            user_message_string=query_fixing_prompt,
            system_message_string="You are an expert SQL assistant. Review the SQL query for errors and provide corrections with reasoning."
        ))
        
        if fixing_response:
            try: 
                # Parse the response to extract the suggested corrected query and reasoning
                response_json = json.loads(fixing_response)
                fixed_sql_query = response_json.get('generated_sql_query', '').strip()
                fixed_reasoning_list = response_json.get('reasonings', [])
                fixed_reasoning = "\n\n".join(f"- **{type(r).__name__}**: {r}" for r in fixed_reasoning_list)

                # Retry executing the fixed query
                df_fixed_result = execute_sql_query(fixed_sql_query, db_path)
                if df_fixed_result is not None:
                    return df_fixed_result
                else:
                    print("Failed to execute the fixed query.")
                    return None
            except json.JSONDecodeError:
                print("Error decoding response from OpenAI. Please try again.")
                return None

def validate_sql_query(query: str) -> bool:
    """
    Validates that the SQL query is well-formed and safe to execute.
    """
    # Basic validation to check for SELECT and FROM statements
    if "SELECT" in query.upper() and "FROM" in query.upper() and ";" in query:
        return True
    return False







# 3. Reasoning Instructions:
#     - Provide a detailed, structured reasoning to justify the SQL query. This should include:
#         1. **Background**: Describe any initial context or assumptions used to understand the problem.
#         2. **Thought Process**: Break down the problem progressively:
#             - Consider whether Common Table Expressions (CTEs) or subqueries are needed.
#             - Identify which columns are relevant for the `SELECT`, `WHERE`, `GROUP BY`, etc.
#             - Determine potential values for `WHERE` clauses, such as ISSUER_NAME, and map those to database columns.
#             - Assess whether filters or aggregations are necessary.
#             - Identify the time period and grouping conditions.
#         3. **Observations**: Reflect on the reasoning steps, offer insights, and describe how the steps lead to the final query.
#     - Think of this reasoning as the model describing the steps it took to create the query.
#         1. Reasoning you provide should first focus on why a nested query was chosen or why it wasn't chosen.
#         2. It should give a query plan on how to solve this question - explain the mapping of the columns to the words in the input question.
#         3. It should explain each of the clauses and why they are structured the way they are structured. For example, if there is a `GROUP BY`, an explanation should be given as to why it exists.
#         4. If there's any `SUM()` or any other function used it should be explained as to why it was required.
    
#     **Rules:**
#     1. Only use `QUARTER` and `YEAR` in the SQL query, do not use any specific dates. If the user question contains a specific date, please convert this to the appropriate year and quarter.
#     2. Use a `LIKE` clause for partial matching of `ISSUER_NAME` (e.g., WHERE ISSUER_NAME LIKE '%value%').
#     3. All queries must be valid to access a SQLite database (e.g., use the command LIMIT instead of FETCH)
#     4. Use "Y" and "N" instead of "YES" and "NO" in the SQL query (e.g., WHERE IS_DEFAULT = 'Y' instead of WHERE IS_DEFAULT = 'YES').
    
#     **Schema for Output:**
#     - This includes the reasonings schema above as an element
#     - The final response should be a json with `names` as `generated_sql_query` and `reasonings`:
#         1. `generated_sql_query` should provide the SQL query generated in string format.
#         2. `reasonings` should provide the reasoning steps adhering to the reasoning instructions.
#     - This is the final answer.
#     """
#     return system_message