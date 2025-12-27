import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('API-KEY'))

#def generate_context(data):


def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    return response.text

print(ask_gemini("Explain how to run a marathon following Jack Daniels' VDOT system."))