import sys
import json
import traceback
import numpy  as np
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Union, Tuple, List
from pprint import pprint
import os
import sqlglot

# load env variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = API_KEY)

"""# Init OpenAI Client

# Schema

## Chain of Thought Reasoning Schema
"""

class Background(BaseModel):
    """A setup to the background for the user."""
    background: str = Field(description="Background for the user's question", min_length=10)


class Thought(BaseModel):
    """A thought about the user's question."""
    thought: str  = Field(description="Text of the thought.")

class Observation(BaseModel):
    """An observation on the sequence of thoughts and observations generated so far."""
    observation: str = Field(description="An insightful observation on the sequence of thoughts and observations generated so far.")


class Reasonings(BaseModel):
    """Returns a detailed reasoning to the user's question."""

    reasonings: list[Union[Background, Thought, Observation]] = Field(
        description="Reasonings to solve the users questions." )

sample_reasonings=Reasonings(reasonings=[Background(background="The task is to generate SQL from natural language query."),
                                            Thought(thought="First thought", helpful="True"),
                                            Thought(thought="Second thought", helpful="True"),
                                            Thought(thought="Third thought", helpful="True"),
                                            Thought(thought="Fourth thought", helpful="True"),
                                            Thought(thought="Fifth thought", helpful="True"),
                                            Observation(observation="Astute observation")])

sample_reasonings.json()

reasonings_schema_json = Reasonings.schema_json()

"""## SQL Schema"""

class FinalQueryOutput(BaseModel):

    input_sql_query_1: str = Field(
        description=f"""Returns the exact same first query that the user gave as input.""")

    input_sql_query_2: str = Field(
        description=f"""Returns the exact same second query that the user gave as input.""")

    reasonings: list[Union[Background, Thought, Observation]] = Field(
        description="Reasonings to solve the users questions." )

    column_mapping_list: List[Tuple[str, str]] = Field(
        description=f"""Returns the list of the corresponding column names in first sql query, sql 1, which
        corresponds to the column name in the other sql query, sql 2, as a list of tuple entries""")

final_output_schema_json = FinalQueryOutput.schema_json()

from pprint import pprint
pprint(final_output_schema_json, indent=4)

sample_comparison_output = FinalQueryOutput(input_sql_query_1="Select count * as total_count from fact_table",
                                input_sql_query_2="Select count * from fact_table",
                                reasonings=[Background(background="Deadline is near"),
                                            Thought(thought="First thought", helpful="True"),
                                            Thought(thought="Second thought", helpful="True"),
                                            Thought(thought="Third thought", helpful="True"),
                                            Thought(thought="Fourth thought", helpful="True"),
                                            Thought(thought="Fifth thought", helpful="True"),
                                            Observation(observation="Astute observation")],
                                column_mapping_list=[("max_revenue", "maximum_revenue"), ("avg_revenue", "average_revenue")])

sample_comparison_output

sample_comparison_output.json()

final_output_schema_json

"""# GPT Call Function"""

def call_openai_model(system_prompt, user_prompt, model_name, client):

    chat_history = [
        {
            'role': 'system',
            'content': system_prompt
        },
        {
            'role': 'user',
            'content': user_prompt
        },

    ]

    final_response = {}

    try:

        response = client.chat.completions.create(
            model           = model_name,
            messages        = chat_history,
            response_format = {"type":"json_object"}
        )

        final_response = response.choices[0].message.content

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        msg = f"Caught an exception {exc_type}': {exc_value}"
        print(msg)
        traceback.print_tb(exc_traceback)

        response = {
            "content": "An error occured. Please retry your chat. \
                If you keep getting this error, you may be out of OpenAI \
                completion tokens. Contact #help-ai on slack for assistance."
        }
        return response

    return final_response

"""# System Prompt"""

system_prompt_snippet_001 = """
```
You are the most intelligent person in the world.
```
"""

system_prompt_snippet_002 = """

```
You will receive a $500 tip if you follow ALL the instructions specified.
```
"""

system_prompt_snippet_003 = """

```
Instructions
```
Give a column mapping between two equivalent sql statements
which may differ in the names of columns used in the output
and may also differ in the structure, but the overall meaning
and function of the query is meant to be the same.
```

```
Use step by step reasoning and at each step generate thoughts of increasing complexity.
```
"""

system_prompt_snippet_004 = """

```
Getting this answer right is important for my career. Please do your best.
```
"""

system_prompt = f"""
{system_prompt_snippet_001}
{system_prompt_snippet_002}
{system_prompt_snippet_003}
{system_prompt_snippet_004}
"""

print(system_prompt)

"""# User Prompt

## Background and Table Structure
"""

complete_user_prompts = """
```
Task Overview
```
Given two sql queries which are supposed to be equivalent, as inputs,
the task is to give a column mapping between the output columns in one sql query
to the other sql query.
```

```
The mapping is to be generated as a list of tuples.
```

```
For each element of the list which would be a tuple,
the first entry in the tuple would be the column name used in sql query 1,
and the second entry in the tuple would be the corresponding column name in the sql query 2.
```
"""

"""## Reasoning Instructions"""

reasoning_instructions = """
```
1. Reasoning you provide should first focus on whether the input sql queries contain
a nested query or not.
2. It should give a plan on how to solve this question.
3. It should explain each of the clauses and why they are structured the way they are structured.
For example, if there is a `group_by`, an explanation should be given as to why it exists.
```

```
Format the generated sql with proper indentation - the columns in the
(`select` statement should have more indentation than keyword `select`
and so on for each SQL clause.)
```
"""

"""## Thought Instructions"""

thought_instructions = f"""
```
Thought Instructions:
```

```
Generate thoughts of increasing complexity.
Each thought should build on the previous ones and thoughts
should progressively cover the nuances of the problem at hand.
```

```
Generate two separate thoughts, one each for the two input sql queries,
to figure out the list of output columns in each of the sql queries.
```

```
Generate a thought to figure out the list of columns in sql query 1
which are present in both the sql queries.
```

```
Generate a thought to figure out the list of columns in sql query 1
which are in sql query 1 but
which are not present in sql query 2.
```

```
Generate a thought to figure out the list of columns in sql query 1
which are in sql query 2 but
which are not present in sql query 1.
```

```
If the query uses common table expressions or nested queries,
the above thoughts should be generated for each of the CTE separately.
```


```
Closing Thoughts and Observations
```
These should summarize:
1. The structure of the SQL query:
    - This states whether the query has any nested query.
    If so, the structure of the nested query is also mentioned.
    If not, a summary of the function of each of the select`, `where`, `group_by` etc. clauses
    should be mentioned.
2. An explanation of why the mapping is correct.
"""

reasoning_schema_instructions = f"""
```
Use the following JSON Schema as the grammar to create the structure
for the step by step reasoning, and then to
create the final SQL query.
```

```
Schema for Reasoning:
```
{reasonings_schema_json}
```

```
The instructions on how to structure the reasoning is provided below:
```
{thought_instructions}
```

```
Schema for Overall Output:
(This includes the reasonings schema above as an element)
```
{final_output_schema_json}
```

```
The final response should be a json with `names` as
    `input_sql_query_1`,
    `input_sql_query_2`,
    `reasonings`,
    `column_mapping_list`.
```
"""

def get_user_prompt_for_question(input_sql_query_1, input_sql_query_2, input_table_schema, complete_user_prompts):

    user_prompt = f"""
    ```
    Here are the two sql statements that are to be compared:
    ```

    ```
    SQL Query 1:
    ```
    {input_sql_query_1}
    ```

    ```
    SQL Query 2:
    ```
    {input_sql_query_2}
    ```

    ```
    Generate a column mapping corresponding to the given input sql queries
    and the description of the table provided below.
    ```
    {input_table_schema}
    ```

    ```
    Here's a more detailed set of instructions:
    ```
    {complete_user_prompts}
    ```

    ```
    Reasoning as to why the query is correct:
    ```
    {reasoning_instructions}


    {reasoning_schema_instructions}

    ```
    Response for Column Mapping Generation:
    ```
    """
    return user_prompt

"""# Call OpenAI with Chain of Thought

## Test Prompt on Sample Question
"""

input_table_schema_for_db = "data/data_schema2.txt"


def normalize_select_expressions(ast):
#    """
#    Sorts the expressions in the Select clause to make comparisons order-independent.
#    """
    if ast.args.get("expressions"):
        # Sort expressions in the SELECT clause if present
        ast.args["expressions"] = sorted(ast.args["expressions"], key=lambda x: str(x))
    for arg in ast.args.values():
        if isinstance(arg, list):
            for sub_arg in arg:
                normalize_select_expressions(sub_arg)
        elif isinstance(arg, sqlglot.Expression):
            normalize_select_expressions(arg)


def are_queries_ast_similar(query1, query2):
    # Parse both queries into ASTs
    ast1 = sqlglot.parse_one(query1)
    ast2 = sqlglot.parse_one(query2)

    # Normalize the ASTs to ignore SELECT column order
    normalize_select_expressions(ast1)
    normalize_select_expressions(ast2)

    # Calculate a similarity score based on a comparison metric
    similarity_score = calculate_similarity(ast1, ast2)

    return similarity_score

def calculate_similarity(ast1, ast2):
    """
    Calculates similarity as a ratio of matching nodes in two ASTs.
    """
    ast1_nodes = list(ast1.walk())
    ast2_nodes = list(ast2.walk())

    # Compare matching nodes by string representation
    matches = sum(1 for node1, node2 in zip(ast1_nodes, ast2_nodes) if str(node1) == str(node2))
    max_length = max(len(ast1_nodes), len(ast2_nodes))

    return matches / max_length if max_length > 0 else 1.0

easy6 = "What is the currency value of holdings for Tennant Co in Q4 2022?"
easy6_gold = '''SELECT SUM(CURRENCY_VALUE)
FROM FUND_REPORTED_HOLDING
WHERE ISSUER_NAME LIKE '%Tennant Co%' AND YEAR = 2022 AND QUARTER = 4;'''
easy6_model = '''SELECT SUM(CURRENCY_VALUE) AS TotalCurrencyValue
FROM FUND_REPORTED_HOLDING
WHERE ISSUER_NAME LIKE '%Tennant Co%' AND YEAR = 2022 AND QUARTER = 4;'''
easy6_accuracy = are_queries_ast_similar(easy6_gold, easy6_model)

easy7 = "Find the total currency value of holdings for each asset category in Q4 2022."
easy7_gold = '''SELECT ASSET_CAT, SUM(CURRENCY_VALUE) AS TotalCurrencyValue
FROM FUND_REPORTED_HOLDING
WHERE YEAR = 2022 AND QUARTER = 4
GROUP BY ASSET_CAT;'''
easy7_model = '''SELECT ASSET_CAT, SUM(CURRENCY_VALUE) AS TotalCurrencyValue
FROM FUND_REPORTED_HOLDING
WHERE YEAR = 2022 AND QUARTER = 4
GROUP BY ASSET_CAT;'''
easy7_accuracy = are_queries_ast_similar(easy7_gold,easy7_model)

easy8 = "Which funds had liabilities greater than $10M in Q2 2023?"
easy8_gold = '''SELECT SERIES_NAME
FROM FUND_REPORTED_INFO
WHERE TOTAL_LIABILITIES > 10000000 AND YEAR = 2023 AND QUARTER = 2;'''
easy8_model = '''SELECT SERIES_NAME, TOTAL_LIABILITIES
FROM FUND_REPORTED_INFO
WHERE TOTAL_LIABILITIES > 10000000 AND YEAR = 2023 AND QUARTER = 2;'''
easy8_accuracy = are_queries_ast_similar(easy8_gold,easy8_model)

easy9 = "What is the cumulative DV01 for 10-year bonds across all funds in Q4 2022?"
easy9_gold = '''SELECT SUM(INTRST_RATE_CHANGE_10YR_DV01) AS Cumulative_DV01_10YR
FROM INTEREST_RATE_RISK
WHERE YEAR = 2022 AND QUARTER = 4;'''
easy9_model = '''SELECT SUM(INTRST_RATE_CHANGE_10YR_DV01) AS Cumulative_DV01_10YR
FROM INTEREST_RATE_RISK
WHERE YEAR = 2022 AND QUARTER = 4;'''
easy9_accuracy = are_queries_ast_similar(easy9_gold,easy9_model)

easy10 = "Find the maturity dates for repurchase agreements in 2022 Q3."
easy10_gold = '''SELECT MATURITY_DATE
FROM REPURCHASE_AGREEMENT
WHERE YEAR = 2022 AND QUARTER = 3;'''
easy10_model = '''SELECT MATURITY_DATE
FROM REPURCHASE_AGREEMENT
WHERE YEAR = 2022 AND QUARTER = 3;'''
easy10_accuracy = are_queries_ast_similar(easy10_gold,easy10_model)

easy11 = "What are the top 5 funds by net assets for Q2 2023?"
easy11_gold = '''SELECT SERIES_NAME, NET_ASSETS
FROM FUND_REPORTED_INFO
WHERE YEAR = 2023 AND QUARTER = 2
ORDER BY NET_ASSETS DESC
LIMIT 5;'''
easy11_model = '''SELECT SERIES_NAME, NET_ASSETS
FROM FUND_REPORTED_INFO
WHERE YEAR = 2023 AND QUARTER = 2
ORDER BY NET_ASSETS DESC
LIMIT 5;'''
easy11_accuracy = are_queries_ast_similar(easy11_gold,easy11_model)

easy12 = "How many debt securities with a fixed coupon type were in default in 2020?"
easy12_gold = '''SELECT COUNT(*)
FROM DEBT_SECURITY
WHERE YEAR = 2020 AND COUPON_TYPE = 'Fixed' AND IS_DEFAULT = 'Y';'''
easy12_model = '''SELECT COUNT(*) AS NumberOfDebtSecuritiesInDefault
FROM DEBT_SECURITY
WHERE COUPON_TYPE = 'Fixed' AND IS_DEFAULT = 'Y' AND YEAR = 2020;'''
easy12_accuracy = are_queries_ast_similar(easy12_gold,easy12_model)

easy13 = "Find the aggregate liabilities and assets grouped by series for Q1 2023."
easy13_gold = '''SELECT SERIES_NAME, SUM(TOTAL_LIABILITIES) AS TotalLiabilities, SUM(TOTAL_ASSETS) AS TotalAssets
FROM FUND_REPORTED_INFO
WHERE YEAR = 2023 AND QUARTER = 1
GROUP BY SERIES_NAME;'''
easy13_model = '''SELECT SERIES_NAME, SUM(TOTAL_ASSETS) AS TotalAssets, SUM(TOTAL_LIABILITIES) AS TotalLiabilities
FROM FUND_REPORTED_INFO
WHERE YEAR = 2023 AND QUARTER = 1
GROUP BY SERIES_NAME;'''
easy13_accuracy = are_queries_ast_similar(easy13_gold,easy13_model)

medium8 = "Identify the top 4 funds by unrealized appreciation in derivative contracts for Q4 2019."
medium8_gold = '''SELECT fri.SERIES_NAME, SUM(ffnc.UNREALIZED_APPRECIATION) AS TotalUnrealizedAppreciation
FROM FUND_REPORTED_INFO fri
JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
JOIN FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc ON frh.HOLDING_ID = ffnc.HOLDING_ID
WHERE fri.YEAR = 2019 AND fri.QUARTER = 4
GROUP BY fri.SERIES_NAME
ORDER BY TotalUnrealizedAppreciation DESC
LIMIT 4;'''
medium8_model = '''SELECT fri.SERIES_NAME, SUM(ffnc.UNREALIZED_APPRECIATION) AS UnrealizedAppreciation
FROM FUND_REPORTED_INFO fri
JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
JOIN FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc ON frh.HOLDING_ID = ffnc.HOLDING_ID
WHERE fri.YEAR = 2019 AND fri.QUARTER = 4
GROUP BY fri.SERIES_NAME
ORDER BY UnrealizedAppreciation DESC
LIMIT 4;'''
medium8_accuracy = are_queries_ast_similar(medium8_gold,medium8_model)

medium9 = "List the funds with their notional amounts grouped by currency in Q4 2019."
medium9_gold = '''SELECT fri.SERIES_NAME, dric.CURRENCY_CODE, SUM(dric.NOTIONAL_AMOUNT) AS TotalNotionalAmount
FROM DESC_REF_INDEX_COMPONENT dric
JOIN FUND_REPORTED_HOLDING frh ON dric.HOLDING_ID = frh.HOLDING_ID
JOIN FUND_REPORTED_INFO FRI ON frh.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
WHERE frh.YEAR = 2019 AND frh.QUARTER = 4
GROUP BY fri.SERIES_NAME, dric.CURRENCY_CODE;'''
medium9_model = '''SELECT FRI.SERIES_NAME, DRIC.CURRENCY_CODE, SUM(DRIC.NOTIONAL_AMOUNT) AS TOTAL_NOTIONAL_AMOUNT
FROM DESC_REF_INDEX_COMPONENT DRIC
JOIN FUND_REPORTED_HOLDING FRH ON DRIC.HOLDING_ID = FRH.HOLDING_ID
JOIN FUND_REPORTED_INFO FRI ON FRH.ACCESSION_NUMBER = FRI.ACCESSION_NUMBER
WHERE FRI.YEAR = 2019 AND FRI.QUARTER = 4
GROUP BY FRI.SERIES_NAME, DRIC.CURRENCY_CODE;'''
medium9_accuracy = are_queries_ast_similar(medium9_gold,medium9_model)

medium10 = "Which funds reported interest rate risks with a 30-year DV01 greater than $10,000 in Q2 2022?"
medium10_gold = '''SELECT fri.SERIES_NAME
FROM FUND_REPORTED_INFO fri
JOIN INTEREST_RATE_RISK irr ON fri.ACCESSION_NUMBER = irr.ACCESSION_NUMBER
WHERE irr.INTRST_RATE_CHANGE_30YR_DV01 > 10000 AND irr.YEAR = 2022 AND irr.QUARTER = 2;'''
medium10_model = '''SELECT DISTINCT fri.SERIES_NAME
FROM INTEREST_RATE_RISK irr
JOIN FUND_REPORTED_INFO fri ON irr.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
WHERE irr.INTRST_RATE_CHANGE_30YR_DV01 > 10000 AND irr.YEAR = 2022 AND irr.QUARTER = 2;'''
medium10_accuracy = are_queries_ast_similar(medium10_gold,medium10_model)

medium11 = "List funds with repurchase agreements involving collateral values exceeding $5M in Q1 2020."
medium11_gold = '''SELECT DISTINCT fri.SERIES_NAME
FROM FUND_REPORTED_INFO fri
JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
JOIN REPURCHASE_COLLATERAL rc ON frh.HOLDING_ID = rc.HOLDING_ID
WHERE rc.COLLATERAL_AMOUNT > 5000000 AND rc.YEAR = 2020 AND rc.QUARTER = 1;'''
medium11_model = '''SELECT DISTINCT fri.SERIES_NAME
FROM FUND_REPORTED_INFO fri
JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
JOIN REPURCHASE_AGREEMENT ra ON frh.HOLDING_ID = ra.HOLDING_ID
JOIN REPURCHASE_COLLATERAL rc ON ra.HOLDING_ID = rc.HOLDING_ID
WHERE rc.COLLATERAL_AMOUNT > 5000000
  AND fri.YEAR = 2020
  AND fri.QUARTER = 1;'''
medium11_accuracy = are_queries_ast_similar(medium11_gold,medium11_model)

medium12 = "List funds that reported a 10-year interest rate risk DV01 greater than $15,000 in Q1 2023."
medium12_gold = '''SELECT DISTINCT fri.SERIES_NAME
FROM FUND_REPORTED_INFO fri
JOIN INTEREST_RATE_RISK irr ON fri.ACCESSION_NUMBER = irr.ACCESSION_NUMBER
WHERE irr.INTRST_RATE_CHANGE_10YR_DV01 > 15000 AND fri.YEAR = 2023 AND fri.QUARTER = 1;'''
medium12_model = '''SELECT DISTINCT FRI.SERIES_NAME
FROM INTEREST_RATE_RISK IRR
JOIN FUND_REPORTED_INFO FRI ON IRR.ACCESSION_NUMBER = FRI.ACCESSION_NUMBER
WHERE IRR.INTRST_RATE_CHANGE_10YR_DV01 > 15000
AND IRR.YEAR = 2023
AND IRR.QUARTER = 1;'''
medium12_accuracy = are_queries_ast_similar(medium12_gold,medium12_model)

medium13 = "Which top 10 securities had the highest change in the total balance of shares between Q2 2021 and Q3 2022?"
medium13_gold = '''SELECT curr.ISSUER_LEI, curr.ISSUER_NAME, (SUM(curr.BALANCE) - SUM(prev.BALANCE)) AS ShareChange
FROM FUND_REPORTED_HOLDING curr
JOIN FUND_REPORTED_HOLDING prev ON curr.ISSUER_LEI = prev.ISSUER_LEI
WHERE curr.YEAR = 2022 AND curr.QUARTER = 3 AND prev.YEAR = 2021 AND prev.QUARTER = 2
GROUP BY curr.ISSUER_LEI, curr.ISSUER_NAME
ORDER BY ABS(SUM(curr.BALANCE) - SUM(prev.BALANCE)) DESC
LIMIT 10;'''
medium13_model = '''SELECT
    frh.ISSUER_NAME,
    ABS(SUM(CASE WHEN frh.QUARTER = 2 AND frh.YEAR = 2021 THEN frh.BALANCE ELSE 0 END) - SUM(CASE WHEN frh.QUARTER = 3 AND frh.YEAR = 2022 THEN frh.BALANCE ELSE 0 END)) AS BalanceChange
FROM FUND_REPORTED_HOLDING frh
WHERE (frh.YEAR = 2021 AND frh.QUARTER = 2) OR (frh.YEAR = 2022 AND frh.QUARTER = 3)
GROUP BY frh.ISSUER_NAME
ORDER BY BalanceChange DESC
LIMIT 10;'''
medium13_accuracy = are_queries_ast_similar(medium13_gold,medium13_model)

hard8 = "Find the funds with net assets greater than one hundred times the maximum unrealized appreciation in Q1 2020."
hard8_gold = '''SELECT SERIES_NAME
FROM FUND_REPORTED_INFO
WHERE NET_ASSETS > 100 * (
    SELECT MAX(UNREALIZED_APPRECIATION)
    FROM FUT_FWD_NONFOREIGNCUR_CONTRACT
    WHERE YEAR = 2020 AND QUARTER = 1
)
AND YEAR = 2020 AND QUARTER = 1;'''
hard8_model = '''SELECT fri.SERIES_NAME, fri.NET_ASSETS
FROM FUND_REPORTED_INFO fri
WHERE fri.YEAR = 2020 AND fri.QUARTER = 1 AND fri.NET_ASSETS > (
    SELECT MAX(UNREALIZED_APPRECIATION) * 100
    FROM FUT_FWD_NONFOREIGNCUR_CONTRACT
    WHERE YEAR = 2020 AND QUARTER = 1
);'''
hard8_accuracy = are_queries_ast_similar(hard8_gold,hard8_model)

# Hard9 = "List the funds with non-cash collateral where total assets are less than the sum of values from index components in Q2 2024."
# hard9_gold = '''SELECT SERIES_NAME
# FROM FUND_REPORTED_INFO
# WHERE IS_NON_CASH_COLLATERAL = 'Y' AND TOTAL_ASSETS < (
#     SELECT SUM(dric.VALUE)
#     FROM DESC_REF_INDEX_COMPONENT dric
#     WHERE dric.YEAR = 2024 AND dric.QUARTER = 2
# )
# AND YEAR = 2024 AND QUARTER = 2;'''
# hard9_model = '''SELECT fri.SERIES_NAME
# FROM FUND_REPORTED_INFO fri
# JOIN DESC_REF_INDEX_COMPONENT dric ON fri.ACCESSION_NUMBER = dric.ACCESSION_NUMBER
# WHERE fri.IS_NON_CASH_COLLATERAL = 'Y' AND fri.QUARTER = 2 AND fri.YEAR = 2024
# GROUP BY fri.SERIES_NAME, fri.TOTAL_ASSETS
# HAVING fri.TOTAL_ASSETS < SUM(dric.VALUE);'''
# hard9_accuracy = are_queries_ast_similar(hard9_gold,hard9_model)

# Hard10 = "Identify the funds that reported derivatives with a notional amount greater than the average notional amount across all funds, and where the sum of their total liabilities exceeds the sum of unrealized appreciation for derivatives in 2019."
# hard10_gold = '''SELECT DISTINCT fri.SERIES_NAME
# FROM FUND_REPORTED_INFO fri
# JOIN FUND_REPORTED_HOLDING frh ON fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
# JOIN DESC_REF_INDEX_COMPONENT dric ON frh.HOLDING_ID = dric.HOLDING_ID
# WHERE dric.NOTIONAL_AMOUNT > (
#     SELECT AVG(NOTIONAL_AMOUNT)
#     FROM DESC_REF_INDEX_COMPONENT
#     WHERE YEAR = 2019
# )
# AND fri.TOTAL_LIABILITIES > (
#     SELECT SUM(UNREALIZED_APPRECIATION)
#     FROM FUT_FWD_NONFOREIGNCUR_CONTRACT
#     WHERE YEAR = 2019
# )
# AND fri.YEAR = 2019;'''
# hard10_model = '''SELECT fri.SERIES_NAME
# FROM FUND_REPORTED_INFO fri
# JOIN OTHER_DERIV_NOTIONAL_AMOUNT odna ON fri.ACCESSION_NUMBER = odna.ACCESSION_NUMBER
# WHERE odna.YEAR = 2019
# GROUP BY fri.SERIES_NAME
# HAVING AVG(odna.NOTIONAL_AMOUNT) < (
#     SELECT AVG(NOTIONAL_AMOUNT)
#     FROM OTHER_DERIV_NOTIONAL_AMOUNT
#     WHERE YEAR = 2019
# ) AND SUM(fri.TOTAL_LIABILITIES) > (
#     SELECT SUM(ffnc.UNREALIZED_APPRECIATION)
#     FROM FUT_FWD_NONFOREIGNCUR_CONTRACT ffnc
#     WHERE ffnc.YEAR = 2019
#     AND ffnc.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
# );'''
# hard10_accuracy = are_queries_ast_similar(hard10_gold,hard10_model)

hard11 = "Find the funds with total assets greater than twice the average unrealized depreciation in Q2 2024."
hard11_gold = '''SELECT SERIES_NAME
FROM FUND_REPORTED_INFO
WHERE TOTAL_ASSETS > 2 * (
    SELECT AVG(UNREALIZED_APPRECIATION)
    FROM FUT_FWD_NONFOREIGNCUR_CONTRACT
    WHERE YEAR = 2024 AND QUARTER = 2
)
AND YEAR = 2024 AND QUARTER = 2;'''
hard11_model = '''SELECT SERIES_NAME, TOTAL_ASSETS
FROM FUND_REPORTED_INFO
WHERE TOTAL_ASSETS > (SELECT 2 * AVG(NET_UNREALIZE_AP_NONDERIV_MON1 + NET_UNREALIZE_AP_NONDERIV_MON2 + NET_UNREALIZE_AP_NONDERIV_MON3)
                      FROM FUND_REPORTED_INFO
                      WHERE QUARTER = 2 AND YEAR = 2024)
AND QUARTER = 2 AND YEAR = 2024;'''
hard11_accuracy = are_queries_ast_similar(hard11_gold,hard11_model)

# Hard12 = "Find funds that reported more derivative contracts than the average number of derivatives across all funds in Q4 2019."
# hard12_gold = '''SELECT fri.SERIES_NAME
# FROM FUND_REPORTED_INFO fri
# WHERE (
#     SELECT COUNT(*)
#     FROM DERIVATIVE_COUNTERPARTY dc
#     JOIN FUND_REPORTED_HOLDING frh ON dc.HOLDING_ID = frh.HOLDING_ID
#     WHERE frh.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
#     AND dc.YEAR = 2019 AND dc.QUARTER = 4
# ) > (
#     SELECT AVG(derivative_count)
#     FROM (
#         SELECT COUNT(*) AS derivative_count
#         FROM DERIVATIVE_COUNTERPARTY dc
#         JOIN FUND_REPORTED_HOLDING frh ON dc.HOLDING_ID = frh.HOLDING_ID
#         WHERE dc.YEAR = 2019 AND dc.QUARTER = 4
#         GROUP BY frh.ACCESSION_NUMBER
#     ) subquery
# )
# AND fri.YEAR = 2019 AND fri.QUARTER = 4;'''
# hard12_model = '''SELECT fri.SERIES_NAME, COUNT(dric.HOLDING_ID) AS NumberOfDerivatives
# FROM FUND_REPORTED_INFO fri
# JOIN DESC_REF_INDEX_COMPONENT dric ON fri.ACCESSION_NUMBER = dric.ACCESSION_NUMBER
# WHERE fri.YEAR = 2019 AND fri.QUARTER = 4
# GROUP BY fri.SERIES_NAME
# HAVING COUNT(dric.HOLDING_ID) > (
#     SELECT AVG(DerivativeCount)
#     FROM (
#         SELECT COUNT(dric.HOLDING_ID) AS DerivativeCount
#         FROM FUND_REPORTED_INFO fri
#         JOIN DESC_REF_INDEX_COMPONENT dric ON fri.ACCESSION_NUMBER = dric.ACCESSION_NUMBER
#         WHERE fri.YEAR = 2019 AND fri.QUARTER = 4
#         GROUP BY fri.SERIES_NAME
#     ) AS AverageDerivatives
# );'''
# hard12_accuracy = are_queries_ast_similar(hard12_gold,hard12_model)

hard13 = "Find funds where borrowers are associated with holdings reported in Q1 2023."
hard13_gold = '''SELECT fri.SERIES_NAME
FROM FUND_REPORTED_INFO fri
WHERE EXISTS (
    SELECT 1
    FROM BORROWER b
    JOIN FUND_REPORTED_HOLDING frh ON b.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
    WHERE fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
    AND b.YEAR = 2023 AND b.QUARTER = 1
)
AND fri.YEAR = 2023 AND fri.QUARTER = 1;'''
hard13_model = '''SELECT DISTINCT fri.SERIES_NAME
FROM FUND_REPORTED_HOLDING frh
JOIN BORROWER b ON frh.ACCESSION_NUMBER = b.ACCESSION_NUMBER
JOIN FUND_REPORTED_INFO fri ON frh.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
WHERE frh.YEAR = 2023 AND frh.QUARTER = 1;'''
hard13_accuracy = are_queries_ast_similar(hard13_gold,hard13_model)

# Hard14 = "Find the funds that reported forward foreign currency contracts where the currency sold was USD in the year 2020."
# hard14_gold = '''SELECT fri.SERIES_NAME
# FROM FUND_REPORTED_INFO fri
# WHERE EXISTS (
#     SELECT 1
#     FROM FWD_FOREIGNCUR_CONTRACT_SWAP fcs
#     JOIN FUND_REPORTED_HOLDING frh ON fcs.HOLDING_ID = frh.HOLDING_ID
#     WHERE fri.ACCESSION_NUMBER = frh.ACCESSION_NUMBER
#     AND fcs.DESC_CURRENCY_SOLD = 'USD'
#     AND fcs.YEAR = 2020
# )
# AND fri.YEAR = 2020;'''
# hard14_model = '''SELECT DISTINCT fri.SERIES_NAME
# FROM FWD_FOREIGNCUR_CONTRACT_SWAP ffcc
# JOIN FUND_REPORTED_INFO fri ON ffcc.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
# WHERE ffcc.DESC_CURRENCY_SOLD = 'USD' AND ffcc.YEAR = 2020;'''
# hard14_accuracy = are_queries_ast_similar(hard14_gold,hard14_model)

hard15 = "Find the funds where the interest rate risk is greater than 10 times the smallest risk amount reported in Q3 2023."
hard15_gold = '''WITH MinRisk AS (
    SELECT
        MIN(INTRST_RATE_CHANGE_3MON_DV01) AS MIN_3MON,
        MIN(INTRST_RATE_CHANGE_1YR_DV01) AS MIN_1YR,
        MIN(INTRST_RATE_CHANGE_5YR_DV01) AS MIN_5YR,
        MIN(INTRST_RATE_CHANGE_10YR_DV01) AS MIN_10YR,
        MIN(INTRST_RATE_CHANGE_30YR_DV01) AS MIN_30YR
    FROM INTEREST_RATE_RISK
    WHERE YEAR = 2023 AND QUARTER = 3
)
SELECT fri.SERIES_NAME
FROM FUND_REPORTED_INFO fri
WHERE EXISTS (
    SELECT 1
    FROM INTEREST_RATE_RISK irr, MinRisk
    WHERE irr.ACCESSION_NUMBER = fri.ACCESSION_NUMBER
    AND (
        irr.INTRST_RATE_CHANGE_3MON_DV01 > 10 * MinRisk.MIN_3MON OR
        irr.INTRST_RATE_CHANGE_1YR_DV01 > 10 * MinRisk.MIN_1YR OR
        irr.INTRST_RATE_CHANGE_5YR_DV01 > 10 * MinRisk.MIN_5YR OR
        irr.INTRST_RATE_CHANGE_10YR_DV01 > 10 * MinRisk.MIN_10YR OR
        irr.INTRST_RATE_CHANGE_30YR_DV01 > 10 * MinRisk.MIN_30YR
    )
    AND irr.YEAR = 2023 AND irr.QUARTER = 3
)
AND fri.YEAR = 2023 AND fri.QUARTER = 3;'''
hard15_model = '''
SELECT DISTINCT fr.ACCESSION_NUMBER, fr.SERIES_NAME
FROM FUND_REPORTED_INFO fr
JOIN INTEREST_RATE_RISK irr ON fr.ACCESSION_NUMBER = irr.ACCESSION_NUMBER
WHERE (irr.INTRST_RATE_CHANGE_3MON_DV01 > 10 * (SELECT MIN(INTRST_RATE_CHANGE_3MON_DV01) FROM INTEREST_RATE_RISK WHERE YEAR = 2023 AND QUARTER = 3)
    OR irr.INTRST_RATE_CHANGE_1YR_DV01 > 10 * (SELECT MIN(INTRST_RATE_CHANGE_1YR_DV01) FROM INTEREST_RATE_RISK WHERE YEAR = 2023 AND QUARTER = 3)
    OR irr.INTRST_RATE_CHANGE_5YR_DV01 > 10 * (SELECT MIN(INTRST_RATE_CHANGE_5YR_DV01) FROM INTEREST_RATE_RISK WHERE YEAR = 2023 AND QUARTER = 3)
    OR irr.INTRST_RATE_CHANGE_10YR_DV01 > 10 * (SELECT MIN(INTRST_RATE_CHANGE_10YR_DV01) FROM INTEREST_RATE_RISK WHERE YEAR = 2023 AND QUARTER = 3)
    OR irr.INTRST_RATE_CHANGE_30YR_DV01 > 10 * (SELECT MIN(INTRST_RATE_CHANGE_30YR_DV01) FROM INTEREST_RATE_RISK WHERE YEAR = 2023 AND QUARTER = 3))
AND irr.YEAR = 2023 AND irr.QUARTER = 3;
'''
hard15_accuracy = are_queries_ast_similar(hard15_gold,hard15_model)

questions = [easy6, easy7, easy8, easy9, easy10, easy11, easy12, easy13, medium8, medium9, medium10, medium11, medium12, medium13, hard8, hard11, hard13, hard15]
gold = [easy6_gold, easy7_gold, easy8_gold, easy9_gold, easy10_gold, easy11_gold, easy12_gold, easy13_gold, medium8_gold, medium9_gold, medium10_gold, medium11_gold, medium12_gold, medium13_gold, hard8_gold, hard11_gold, hard13_gold, hard15_gold]
model = [easy6_model, easy7_model, easy8_model, easy9_model, easy10_model, easy11_model, easy12_model, easy13_model, medium8_model, medium9_model, medium10_model, medium11_model, medium12_model, medium13_model, hard8_model, hard11_model, hard13_model, hard15_model]

def df_accuracy(path_gold, path_model, mapping_list):
    """
    Compares two databases row by row and column by column and calculates an accuracy score.

    Parameters:
        path_gold (str): Path to the gold standard CSV file.
        path_model (str): Path to the model-generated CSV file.

    Returns:
        float: Accuracy score between the two dataframes.
    """
    try:
        # Load the dataframes
        df_gold = pd.read_csv(path_gold)
        df_model = pd.read_csv(path_model)
    except pd.errors.EmptyDataError as e:
        raise ValueError(f"One of the input files is empty: {e}")

    df_model = df_model.iloc[:, 1:]

    # Create dictionaries for mapping from mapping_list
    gold_to_model = {pair[0]: pair[1] for pair in mapping_list if len(pair) == 2}
    model_to_gold = {pair[1]: pair[0] for pair in mapping_list if len(pair) == 2}

    # Columns that are in df_gold but have no mapping to df_model (standalone columns in df_gold)
    gold_only_columns = [pair[0] for pair in mapping_list if len(pair) == 1]

    df_gold_filtered = df_gold[gold_only_columns + list(gold_to_model.keys())]
    df_model_filtered = df_model.rename(columns=model_to_gold)

    # Retain only the columns in df_model that are present in the mapping
    model_columns = list(gold_to_model.values())
    df_model_filtered = df_model_filtered.filter(items=gold_only_columns + model_columns)

    if len(df_gold_filtered.columns) > len(df_model_filtered.columns):
        df_gold_filtered = df_gold_filtered[df_model_filtered.columns]
    elif len(df_model_filtered.columns) > len(df_gold_filtered.columns):
        df_model_filtered = df_model_filtered[df_gold_filtered.columns]

    # # Replace NaN with a consistent value for comparison
    df_gold_filtered.fillna(value=np.nan, inplace=True)
    df_model_filtered.fillna(value=np.nan, inplace=True)

    # Ensure rows are sorted for accurate comparison
    # df_gold_filtered = df_gold_filtered.sort_index().reset_index(drop=True)
    # df_model_filtered = df_model_filtered.sort_index().reset_index(drop=True)

    df_gold_sorted = df_gold_filtered.sort_values(by=df_gold_filtered.columns.tolist()).reset_index(drop=True)
    df_model_sorted = df_model_filtered.sort_values(by=df_model_filtered.columns.tolist()).reset_index(drop=True)

    # Compare rows and calculate accuracy
    matches = (df_gold_sorted.values == df_model_sorted.values).all(axis=1)  # Row-wise match
    accuracy = np.mean(matches)

    return accuracy

easy_sql_accuracy = [easy7_accuracy, easy8_accuracy, easy9_accuracy, easy10_accuracy, easy11_accuracy, easy12_accuracy, easy13_accuracy, medium8_accuracy, medium9_accuracy, medium10_accuracy, medium11_accuracy, medium12_accuracy, medium13_accuracy, hard8_accuracy, hard11_accuracy, hard13_accuracy, hard15_accuracy]
easy_csv_accuracy = []
def easy_accuracy(easy_csv_accuracy, gold, model, input_table_schema_for_db, complete_user_prompts, system_prompt, client, easy_sql_accuracy):
    for i in range(6, 14):
        path_gold = f"DB CSVs/Easy{i}.csv"
        path_model = f"Model CSVs/Easy{i}.csv"

        user_prompt = get_user_prompt_for_question(gold[i-6],
                                                    model[i-6],
                                                    input_table_schema_for_db,
                                                    complete_user_prompts)

        response        = call_openai_model(system_prompt = system_prompt,
                                    user_prompt   = user_prompt,
                                    model_name    = 'gpt-4o', client=client)

        response_parsed = json.loads(response)

        try:
            accuracy = df_accuracy(path_gold, path_model, response_parsed["column_mapping_list"])
            easy_csv_accuracy.append(accuracy)
        except Exception as e:
            # Handle any exception by setting accuracy to 0 and logging the error
            accuracy = 0
            easy_csv_accuracy.append(accuracy)

        print(f"Accuracy for Easy{i}: {accuracy:.2f}")
    
    avg_easy_db_acc = round((sum(easy_csv_accuracy) / len(easy_csv_accuracy)), 2)
    avg_easy_sql_acc = round((sum(easy_sql_accuracy) / len(easy_sql_accuracy)), 2)
    avg_combined_easy_acc = round(((avg_easy_db_acc + avg_easy_sql_acc) / 2), 2)
    print("\nAccuracy for Easy CSVs: " + str(avg_easy_db_acc))
    print("Accuracy for Easy SQL Queries: " + str(avg_easy_sql_acc))
    print("Combined Accuracy for Easy: " + str(avg_combined_easy_acc) + "\n")
    return avg_combined_easy_acc, avg_easy_db_acc, avg_easy_sql_acc

medium_sql_accuracy = [medium8_accuracy, medium9_accuracy, medium10_accuracy, medium11_accuracy, medium12_accuracy, medium13_accuracy]
medium_csv_accuracy = []
def medium_accuracy(med_csv_accuracy, gold, model, input_table_schema_for_db, complete_user_prompts, system_prompt, client, med_sql_accuracy):
    for i in range(8, 14):
        path_gold = f"DB CSVs/Medium{i}.csv"
        path_model = f"Model CSVs/Medium{i}.csv"

        user_prompt = get_user_prompt_for_question(gold[i],
                                                    model[i],
                                                    input_table_schema_for_db,
                                                    complete_user_prompts)

        response        = call_openai_model(system_prompt = system_prompt,
                                    user_prompt   = user_prompt,
                                    model_name    = 'gpt-4o', client=client)

        response_parsed = json.loads(response)

        try:
            accuracy = df_accuracy(path_gold, path_model, response_parsed["column_mapping_list"])
            med_csv_accuracy.append(accuracy)
        except Exception as e:
            # Handle any exception by setting accuracy to 0 and logging the error
            accuracy = 0
            med_csv_accuracy.append(accuracy)
        
        print(f"Accuracy for Medium{i}: {accuracy:.2f}")
    
    avg_med_db_acc = round((sum(med_csv_accuracy) / len(med_csv_accuracy)), 2)
    avg_med_sql_acc = round((sum(med_sql_accuracy) / len(med_sql_accuracy)), 2)
    avg_combined_med_acc = round(((avg_med_db_acc + avg_med_sql_acc) / 2), 2)
    print("\nAccuracy for Medium CSVs: " + str(avg_med_db_acc))
    print("Accuracy for Medium SQL Queries: " + str(avg_med_sql_acc))
    print("Combined Accuracy for Medium: " + str(avg_combined_med_acc) + "\n")
    return avg_combined_med_acc, avg_med_db_acc, avg_med_sql_acc

hard_sql_accuracy = [hard8_accuracy, hard11_accuracy, hard13_accuracy, hard15_accuracy]
hard_csv_accuracy = []
def hard_accuracy(hard_csv_accuracy, gold, model, input_table_schema_for_db, complete_user_prompts, system_prompt, client, hard_sql_accuracy):
    idx = 14
    for i in [8, 11, 13, 15]:
        path_gold = f"DB CSVs/Hard{i}.csv"
        path_model = f"Model CSVs/Hard{i}.csv"

        user_prompt = get_user_prompt_for_question(gold[idx],
                                                    model[idx],
                                                    input_table_schema_for_db,
                                                    complete_user_prompts)

        response        = call_openai_model(system_prompt = system_prompt,
                                    user_prompt   = user_prompt,
                                    model_name    = 'gpt-4o', client=client)

        response_parsed = json.loads(response)

        try:
            accuracy = df_accuracy(path_gold, path_model, response_parsed["column_mapping_list"])
            hard_csv_accuracy.append(accuracy)
        except Exception as e:
            # Handle any exception by setting accuracy to 0 and logging the error
            accuracy = 0
            hard_csv_accuracy.append(accuracy)

        print(f"Accuracy for Hard{i}: {accuracy:.2f}")
        idx += 1
    
    avg_hard_db_acc = round((sum(hard_csv_accuracy) / len(hard_csv_accuracy)), 2)
    avg_hard_sql_acc = round((sum(hard_sql_accuracy) / len(hard_sql_accuracy)), 2)
    avg_combined_hard_acc = round(((avg_hard_db_acc + avg_hard_sql_acc) / 2), 2)
    print("\nAccuracy for Hard CSVs: " + str(avg_hard_db_acc))
    print("Accuracy for Hard SQL Queries: " + str(avg_hard_sql_acc))
    print("Combined Accuracy for Hard: " + str(avg_combined_hard_acc) + "\n")
    return avg_combined_hard_acc, avg_hard_db_acc, avg_hard_sql_acc

easy, easy_csv, easy_sql = easy_accuracy(easy_csv_accuracy, gold, model, input_table_schema_for_db, complete_user_prompts, system_prompt, client, easy_sql_accuracy)
medium, medium_csv, medium_sql = medium_accuracy(medium_csv_accuracy, gold, model, input_table_schema_for_db, complete_user_prompts, system_prompt, client, medium_sql_accuracy)
#hard, hard_csv, hard_sql = hard_accuracy(hard_csv_accuracy, gold, model, input_table_schema_for_db, complete_user_prompts, system_prompt, client, hard_sql_accuracy)

print("****SUMMARY****")
print("Easy Accuracy: " + str(easy))
print("Medium Accuracy: " + str(medium))
#print("Hard Accuracy: " + str(hard))

#csv_accuracy = round(((easy_csv + medium_csv + hard_csv) / 3), 2)
#print("\nOverall Output Accuracy: " + str(csv_accuracy))

#sql_accuracy = round(((easy_sql + medium_sql + hard_sql) / 3), 2)
#print("\nOverall SQL Accuracy: " + str(sql_accuracy))

#accuracy = round(((easy + medium + hard) / 3), 2)
#print("\nOverall Model Accuracy: " + str(accuracy))