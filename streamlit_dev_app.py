import os
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from transformers import pipeline

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

# Function to read HTML content directly from an UploadedFile object
def get_content_from_uploaded_file(uploaded_file):
    # To read file as string:
    stringio = uploaded_file.getvalue()
    string_data = stringio.decode("utf-8")
    return string_data

# Function to generate content using OpenAI's GPT model
def generate_content(code_content, user_prompt, previous_messages, selected_model, max_tokens=1500, temperature=0):
    # Include the HTML content in the user prompt
    full_prompt = f"The following is a code snippet:\n{code_content}\n\n{user_prompt}"

    # Append the new user prompt to the message history
    message_history = previous_messages.copy()
    message_history.append({"role": "user", "content": full_prompt})

    # Check which model is selected and generate the response accordingly
    if 'OpenAI' in selected_model:
        model = model_options[selected_model]
        gpt_response = client.chat.completions.create(
            model=model,
            messages=message_history,  # Include previous messages for context.
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # Extract the content from the response
        response = gpt_response.choices[0].message.content
    else:
        # For Hugging Face models
        response = generate_content_huggingface(full_prompt, model_name=model_options[selected_model], max_tokens=max_tokens)

    # Append GPT's response to the message history
    message_history.append({"role": "assistant", "content": response})
    return response, message_history


# Function to generate content using Hugging Face's model
def generate_content_huggingface(prompt, model_name="codellama/CodeLlama-70b-hf", max_tokens=1500):
    generator = pipeline('text-generation', model=model_name)
    response = generator(prompt, max_length=max_tokens)[0]
    return response['generated_text']

# Model options are defined here so they are available before they are needed
model_options = {
    'OpenAI GPT-4': 'gpt-4',
    'OpenAI GPT-3.5': 'gpt-3.5-turbo',
    'Hugging Face CodeLlama': 'codellama/CodeLlama-70b-hf'
}

# Session state for preserving message history
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Render the Streamlit interface
st.title("AI Code Assistant")

# Allow the user to select the AI model
selected_model = st.selectbox("Select the AI model:", list(model_options.keys()))

# File uploader for code
uploaded_file = st.file_uploader("Upload a code file:", type=['py', 'txt', 'html', 'js', 'css', 'csv', 'php'])
code_content = ""
if uploaded_file is not None:
    code_content = get_content_from_uploaded_file(uploaded_file)
    language = st.selectbox("Select the code language:", ['Python', 'HTML', 'JavaScript', 'CSS', 'CSV', 'PHP', 'TXT'])
    st.code(code_content, language)

# Prompt for user input
user_prompt = st.text_area("Enter your prompt:", height=150)

# Sending the prompt to the AI
send_button = st.button("Send Prompt")

if send_button and uploaded_file is not None and code_content and user_prompt:
    response, message_history = generate_content(code_content, user_prompt, st.session_state['message_history'], selected_model)
    st.session_state['message_history'].append({"role": "user", "content": user_prompt})
    st.session_state['message_history'].append({"role": "assistant", "content": response})
    st.text_area("AI Response", response, height=300)

# Display message history
st.subheader("Message History")
for message in st.session_state['message_history']:
    role = message['role']
    content = message['content']
    st.write(f"{role}: {content}")

#Función para resumir el historial de mensajes
def summarize_message_history(message_history, model="gpt-3.5-turbo-0125", max_tokens=3000):
    prompt = "Please Summarize the following conversation by extracting the key points in order by sections:\n\n"
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

#Incorporar el botón resumir a la interfaz

if st.button("Resumir"):
    summary = summarize_message_history(st.session_state['message_history'])
    st.text_area("Resumen", summary, height=300)
    # Guardar el resumen en un archivo txt
    with open("summary.txt", "w") as file:
        file.write(summary)
    st.success("Resumen guardado en summary.txt.")
