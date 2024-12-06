import tiktoken
from backend import get_user_prompt_for_question  # Import the function from backend.py

def calculate_tokens_for_prompt(input_question: str, model_name: str = "gpt-4-0125-preview"):
    """
    Calculates the number of tokens in the user_message_string for a given model.

    Args:
    - input_question (str): The user's natural language question.
    - model_name (str): The OpenAI model you plan to use. Default is "gpt-4-0125-preview".

    Returns:
    - int: The number of tokens used by the generated user_message_string.
    """
    # Generate the user prompt
    user_message_string = get_user_prompt_for_question(input_question)

    # Use the appropriate encoder for the specified model
    encoder = tiktoken.get_encoding("cl100k_base")  # Use "cl100k_base" for gpt-4-0125-preview

    # Tokenize the input string
    tokens = encoder.encode(user_message_string)
    token_count = len(tokens)

    return token_count, user_message_string


if __name__ == "__main__":
    # Replace this with your specific test question
    test_question = "What is the total amount of assets held by each fund in Q2 of 2023?"

    # Calculate token usage
    token_count, user_message_string = calculate_tokens_for_prompt(test_question)

    # Print the results
    print(f"The generated user_message_string contains {token_count} tokens.\n")
    print("Generated user_message_string:")
    print(user_message_string)
