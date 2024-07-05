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

# Function to read HTML content directly from an UploadedFile object
def get_content_from_uploaded_file(uploaded_file):
    # To read file as string:
    stringio = uploaded_file.getvalue()
    string_data = stringio.decode("utf-8")
    return string_data

# Function to generate content using OpenAI's GPT model
def generate_content(code_content, user_prompt, previous_messages, model="gpt-4-1106-preview", max_tokens=1500, temperature=0):
    # Include the HTML content in the user prompt
    full_prompt = f"The following is a code snippet:\n{code_content}\n\n{user_prompt}"

    # Append the new user prompt to the message history
    message_history = previous_messages.copy()
    message_history.append({"role": "user", "content": full_prompt})

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

# Streamlit interface
st.title("Doc Assistant")

# Acordeón para mostrar el historial de mensajes
with st.expander("Show Message History"):
    if 'message_history' in st.session_state:
        for message in st.session_state['message_history']:
            # Aquí puedes personalizar cómo quieres mostrar los mensajes
            if message['role'] == 'user':
                st.markdown(f"**User:** {message['content']}")
            elif message['role'] == 'assistant':
                st.markdown(f"**Assistant:** {message['content']}")
            else:
                st.markdown(f"**{message['role'].capitalize()}:** {message['content']}")


# File uploader with language option
uploaded_file = st.file_uploader(
    "Choose a source code file",
    type=['html', 'py', 'php', 'js', 'css', 'csv', 'txt']
)

code_content = ""
languages = {
    'Python': 'py',
    'HTML': 'html',
    'PHP': 'php',
    'JavaScript': 'js',
    'CSS': 'css',
    'CSV': 'csv',
    'TXT': 'txt'
}


if uploaded_file is not None:
    code_content = get_content_from_uploaded_file(uploaded_file)
    language = st.selectbox('Select the language', options=list(languages.keys()))
    st.code(code_content, language=languages[language])

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = [
        {"role": "system", "content": f"""Eres un ingeniero de software especializado en el desarrollo de aplicaciones. Tienes el dominio de herramientas como Python, Django, HTML, CSS y Bases de datos. Estas trabajando en un entorno que cuenta con Windows 10 y Pycharm. Cuando propongas código:
- Los comentarios dentro del codigo deben estar en idioma ingles.
- Cuando lo veas conveniente, incluye en los codigos propuestos lo necesario para la gestion de errores."""}
    ]

user_prompt = st.text_area("Ask the assistant for code ideas or any other queries:", height=150)

disabled_button = uploaded_file is None or len(code_content.strip()) == 0
send_button = st.button("Send Prompt", disabled=disabled_button)

if send_button and code_content:
    response, message_history = generate_content(
        code_content, user_prompt, st.session_state['message_history']
    )
    st.session_state['message_history'] = message_history
    st.text_area("Assistant Response", response, height=300)

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