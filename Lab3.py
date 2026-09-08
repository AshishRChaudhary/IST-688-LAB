import streamlit as st
from openai import OpenAI

st.title("Lab 3 - Chatbot with Memory")

MODEL = "gpt-5-nano"
BUFFER_TURNS = 2  # only send the last 2 user/assistant exchanges to the LLM

# Create an OpenAI client once per session.
if "client" not in st.session_state:
    st.session_state.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Full conversation history - this is what gets displayed to the user.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

# Display the full chat history.
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Conversation buffer: only pass the last BUFFER_TURNS exchanges (plus the
    # new question) to the LLM, even though the full history is shown above.
    buffered_messages = st.session_state.messages[-(BUFFER_TURNS * 2 + 1):]

    client = st.session_state.client
    stream = client.chat.completions.create(
        model=MODEL,
        messages=buffered_messages,
        stream=True,
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
