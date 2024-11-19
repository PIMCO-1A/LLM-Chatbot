import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine
from pathlib import Path
from data_loading import load_schema

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# Load the schema
schema_file_path = "Table_Schema.txt"
schema = load_schema(schema_file_path)

def schema_to_string(schema):
    """
    Convert the schema dictionary to a human-readable string for use in prompts.
    """
    schema_str = "\n".join([f"Table: {table}\nColumns: {', '.join(columns)}" for table, columns in schema.items()])
    return schema_str

def openai_message_creator(user_message_string, system_message_string, schema):
    """
    Creates the message payload for the OpenAI API, including schema details in the system message.
    """
    schema_str = schema_to_string(schema)
    # Append schema details to the system message
    system_message_string += f"\n\n### Database Schema:\n{schema_str}"

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
        print("Sending request to OpenAI API...")  # Debugging line
        print("Messages:", messages)  # Debugging line to see the message content
        print("Model:", model)  # Debugging line to check the model used

        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        print("OpenAI API Response", response)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None
