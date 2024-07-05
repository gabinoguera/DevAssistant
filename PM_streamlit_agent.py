import os
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# Intenta cargar las claves API desde Streamlit secrets (solo para producción)
secrets_loaded = False
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    secrets_loaded = True
except FileNotFoundError:
    # Streamlit secrets no se encontraron, estamos probablemente en un entorno de desarrollo local
    pass

# Si las claves no se cargaron desde Streamlit secrets, intenta cargarlas desde .env
if not secrets_loaded:
    _ = load_dotenv(find_dotenv())
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        st.error("No API key found. Please set your OpenAI API key in an .env file for local development.")


# Function to generate content using OpenAI's GPT model
def generate_content(user_prompt, previous_messages, selected_model, max_tokens=1500, temperature=0):
    # Append the new user prompt to the message history
    message_history = previous_messages.copy()
    message_history.append({"role": "user", "content": user_prompt})

    # Check which model is selected and generate the response accordingly
    model = model_options[selected_model]
    gpt_response = client.chat.completions.create(
        model=model,
        messages=message_history,  # Include previous messages for context.
        max_tokens=max_tokens,
        temperature=temperature,
    )
    # Extract the content from the response
    response = gpt_response.choices[0].message.content

    # Append GPT's response to the message history
    message_history.append({"role": "assistant", "content": response})
    return response, message_history


# Model options without Hugging Face CodeLlama
model_options = {
    'OpenAI GPT-4': 'gpt-4',
    'OpenAI GPT-3.5': 'gpt-3.5-turbo'
}

# Session state for preserving message history
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = [
        {"role": "system", "content": f"""You are a Scrum Master specialized in application development. You are proficient in tools such as JIRA, SCRUM, Agile Methodologies, Python, Django, HTML, CSS and databases such as MySQL or Mongo DB. You are working in an environment that has Windows 10 and Pycharm as IDE. When planning the sprint please keep in mind:
- The duration of the sprint should be 15 days.
- The dashboards will be classified as: to do, in progress, blocked, to check or finished.
- It should include the step-by-step actions to achieve the project goal."""}
    ]

# Render the Streamlit interface
st.title("AI Project Manager Assistant")

# Allow the user to select the AI model
selected_model = st.selectbox("Select the AI model:", list(model_options.keys()))

# Prompt for user input
user_prompt = st.text_area("Enter your query or task for the assistant:", height=150)

# Sending the prompt to the AI
send_button = st.button("Send Prompt")

if send_button and user_prompt:
    response, message_history = generate_content(user_prompt, st.session_state['message_history'], selected_model)
    st.session_state['message_history'] = message_history
    st.text_area("AI Response", response, height=300)

# Display message history
st.subheader("Message History")
for message in st.session_state['message_history']:
    role = message['role']
    content = message['content']
    st.write(f"{role}: {content}")


# Function to summarize message history
def summarize_message_history(message_history, model="gpt-3.5-turbo-0125", max_tokens=3000):
    prompt = "From this history write a project called Agents Project with the context, objectives and the development of the project.\n\n"
    for message in message_history:
        role = message["role"]
        content = message["content"]
        prompt += f"{role.capitalize()}: {content}\n"

    gpt_response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
        max_tokens=max_tokens
    )
    summary = gpt_response.choices[0].message.content
    return summary
# This function remains unchanged

# Button to summarize the message history
if st.button("Summarize"):
    summary = summarize_message_history(st.session_state['message_history'])
    st.text_area("Summary", summary, height=300)
    # Save the summary to a text file
    with open("summary.txt", "w") as file:
        file.write(summary)
    st.success("Summary saved in summary.txt.")