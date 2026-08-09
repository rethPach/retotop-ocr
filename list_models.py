import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

print("Available models:")
for m in client.models.list():
    if "generateContent" in m.supported_actions and "flash" in m.name:
        print(m.name)
