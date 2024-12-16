import streamlit as st
import time
# Streamed response emulator
def stream_response(response):
    r2 = response
    for word in r2.split():
        yield word + " "
        time.sleep(0.05)
st.title("PIMCO Bot")
if "messages" not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if prompt := st.chat_input("Enter your prompt:"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    answer = f"PIMBot: {prompt}"
    ## export this prompt variable into the chatbot, append it with the prompt writing piece
    ## potentially trigger run of openai script when prompt is entered?
    ## import response variable (below) at completion
    # Add delay to simulate thinking
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(stream_response(answer))
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
