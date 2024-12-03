import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine
from pathlib import Path
from schema_loader import load_schema
import json
from pydantic import BaseModel
from typing import List

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# Load the schema
schema_file_path = "data/data_schema2.txt"
schema = load_schema(schema_file_path)

class APIResponse(BaseModel):
    content: str

def schema_to_string(schema):
    """
    Convert the schema dictionary to a human-readable string for use in prompts.
    """
    schema_str = "\n".join([f"Table: {table}\nColumns: {', '.join(columns)}" for table, columns in schema.items()])
    return schema_str

def convert_date_to_quarter_year(date):
    """
    Converts a specific date (YYYY-MM-DD) into a quarter and year.
    """
    year, month, _ = map(int, date.split('-'))
    quarter = (month - 1) // 3 + 1
    return year, quarter

def process_prompt_for_quarter_year(prompt):
    """
    Replaces any specific dates or date ranges in the user prompt with corresponding quarter and year.
    """
    import re
    # Match a date in the format YYYY-MM-DD
    date_pattern = r'\b\d{4}-\d{2}-\d{2}\b'
    matches = re.findall(date_pattern, prompt)

    for date in matches:
        year, quarter = convert_date_to_quarter_year(date)
        prompt = prompt.replace(date, f"QUARTER {quarter}, YEAR {year}")
    
    # Optional: Handle explicit date ranges in the text (e.g., 'between April 2020 and June 2020')
    date_range_pattern = r'between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})'
    range_matches = re.findall(date_range_pattern, prompt)
    for start_date, end_date in range_matches:
        start_year, start_quarter = convert_date_to_quarter_year(start_date)
        end_year, end_quarter = convert_date_to_quarter_year(end_date)
        if start_year == end_year:
            prompt = prompt.replace(
                f"between {start_date} and {end_date}",
                f"QUARTER {start_quarter} to {end_quarter}, YEAR {start_year}"
            )
        else:
            prompt = prompt.replace(
                f"between {start_date} and {end_date}",
                f"YEAR {start_year}, QUARTER {start_quarter} to YEAR {end_year}, QUARTER {end_quarter}"
            )
    
    return prompt

def openai_message_creator(user_message_string, system_message_string, schema):
    """
    Creates the message payload for the OpenAI API, including schema details in the system message.
    """
    schema_str = schema_to_string(schema)
    # Append schema details to the system message
    system_message_string += f"\n\n### Database Schema:\n{schema_str}"

    # Process the user prompt to ensure only QUARTER and YEAR are used
    user_message_string = process_prompt_for_quarter_year(user_message_string)

    messages = [
        {"role": "system", "content": system_message_string},
        {"role": "user", "content": user_message_string}
    ]
    return messages

def query_openai(messages, model="gpt-4-0125-preview"):
    """
    Queries the OpenAI API with the provided messages and model.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None




