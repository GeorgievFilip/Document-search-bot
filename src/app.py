from utils import extract_filenames
from dotenv import load_dotenv
import os
import streamlit as st
import requests
from PIL import Image


load_dotenv()

# Use the API_URL from the .env file if available, otherwise default to localhost.
API_URL = os.environ.get('API_URL') or 'http://localhost:3000/dev/questions'

image = Image.open('src/images/osjr3wvz.jpg')
st.image(image, width=100)

user_input = st.text_input("Enter your question:")
if user_input:
    with st.spinner('Generating your answer...'):
        response = requests.post(API_URL, json={"question": user_input})

    if response.status_code == 200:
        response = response.json()
        st.write(response['request']['result'])
        for document_name, document_content in response['relevant_documents'].items():
            with st.expander(extract_filenames(document_name)):
                st.write(document_content)
    else:
        error_message = f"Received status code {response.status_code}"
        try:
            error_content = response.json().get('error', 'No additional information available.')
            error_message += f": {error_content}"
        except Exception:
            error_message += " and could not parse additional error information."

        st.error(error_message)
