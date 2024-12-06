import streamlit as st
import json
from backend import (
    execute_sql_query,
    validate_sql_query,
    query_openai,
    openai_message_creator,
    generate_system_message,
    get_user_prompt_for_question,  
    schema,
    example_prompts_and_queries
)
from pathlib import Path

# Initialize Session State
if "persistent_query_log" not in st.session_state:
    st.session_state.persistent_query_log = []

if "messages" not in st.session_state:
    st.session_state.messages = []

# App Title
st.title("PIMCO Bot")

# Display Persistent Query Log
if st.session_state.persistent_query_log:
    for query_record in st.session_state.persistent_query_log:
        st.write("#### Question")
        st.markdown(query_record["question"])
        st.write("#### SQL Query")
        st.code(query_record["query"], language="sql")
        st.write("#### Reasoning")
        st.markdown(query_record["reasoning"])
        st.write("#### Results")
        st.dataframe(query_record["results"])

# User Input
prompt = st.chat_input("Enter your question about the database:")

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate the full user prompt including reasoning instructions
    user_prompt = get_user_prompt_for_question(prompt)

    # Generate the system message from backend
    system_message_string = generate_system_message()

    # Generate OpenAI messages with schema and examples
    messages = openai_message_creator(
        user_message_string=user_prompt,
        system_message_string=system_message_string,
        schema=schema
    )

    # Query OpenAI
    response = query_openai(messages)

    if response:
        # Assuming response is a well-formed JSON string from OpenAI, parse it
        try:
            response_json = json.loads(response)
            print(f"Full OpenAI Response: {response_json}")

            # Extract the generated SQL query and reasoning
            generated_sql_query = response_json["generated_sql_query"]
            reasoning_dict = response_json["reasonings"]

            # Clean the SQL query before executing it
            cleaned_sql_query = generated_sql_query.replace("```sql", "").replace("```", "").strip()

            print(f"Cleaned SQL Query:\n{cleaned_sql_query}")
            print(f"Reasoning:\n{reasoning_dict}")

            # Check if 'reasonings' is a dict containing 'reasonings' list
            if isinstance(reasoning_dict, dict) and "reasonings" in reasoning_dict:
                reasoning_list = reasoning_dict["reasonings"]
            elif isinstance(reasoning_dict, list):
                reasoning_list = reasoning_dict
            else:
                reasoning_list = []

            # Convert reasoning_list to string for display
            reasoning = ""
            for item in reasoning_list:
                if 'background' in item:
                    reasoning += f"- **Background**: {item['background']}\n"
                if 'thought' in item:
                    reasoning += f"- **Thought**: {item['thought']}\n"
                if 'observation' in item:
                    reasoning += f"- **Observation**: {item['observation']}\n"

            # Validate the cleaned query
            if validate_sql_query(cleaned_sql_query):
                # Execute the cleaned query
                df_result = execute_sql_query(cleaned_sql_query, Path("data/sec_nport_data_combined.db"), prompt)

                if df_result is not None:
                    # Save query, reasoning, and results to persistent query log
                    query_record = {
                        "question": prompt,
                        "query": cleaned_sql_query,
                        "reasoning": reasoning,
                        "results": df_result
                    }
                    st.session_state.persistent_query_log.append(query_record)

                    # Display SQL query, reasoning, and results
                    st.write("#### Question")
                    st.markdown(query_record["question"])
                    st.write("#### SQL Query")
                    st.code(query_record["query"], language="sql")
                    st.write("#### Reasoning")
                    st.markdown(query_record["reasoning"])
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
        except json.JSONDecodeError:
            st.error("Error decoding response from OpenAI. Please try again.")
        except KeyError as e:
            st.error(f"Missing expected key in the response: {e}")
    else:
        st.error("No response from OpenAI. Please try again.")