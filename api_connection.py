import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine
from pathlib import Path


load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

def openai_message_creator(user_message_string, system_message_string):
    system_message_identifier = "system"
    user_message_identifier = "user"

    sys_message_element = {"role": system_message_identifier, "content": system_message_string}
    user_message_element = {"role": user_message_identifier, "content": user_message_string}

    messages = [sys_message_element, user_message_element]
    return messages

# Update the query_openai function for the new API
def query_openai(messages, model="gpt-4-0125-preview"):
    try:
        print("Sending request to OpenAI API...")  # Debugging line
        print("Messages:", messages)  # Debugging line to see the message content
        print("Model:", model)  # Debugging line to check the model used
        # Use the updated API call with "chat.completions.create"
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        print("OpenAI API Response:", response)
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None









