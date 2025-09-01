import os
from typing import Optional
import google.generativeai as genai

# Configure the Gemini client with the API key from the .env file
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

async def generate_gemini_text(prompt: str, model_name: str = "gemini-1.5-flash-latest") -> Optional[str]:
    """
    Generates text using the Gemini API. Returns None if the API key is not set or an error occurs.
    """
    if not api_key:
        print("GEMINI_API_KEY not found. Skipping LLM call.")
        return None

    try:
        model = genai.GenerativeModel(model_name)
        # Use the async version of the call to work with FastAPI
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None
