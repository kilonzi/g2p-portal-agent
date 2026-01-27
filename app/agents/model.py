import logging
from loguru import logger
from google.oauth2 import service_account
from langchain_google_genai import ChatGoogleGenerativeAI
from app.settings import settings


def get_model(tools=None, temperature=0.1):
    """
    Initialize the model (Google Vertex AI or Anthropic).
    """
    credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        
    model = ChatGoogleGenerativeAI(
        model=settings.GOOGLE_GEMINI_MODEL,
        credentials=credentials,
        google_api_key=None, # We use credentials/ADC
        temperature=temperature,
        convert_system_message_to_human=True # Helper for some models
    )
    
    if tools:
        return model.bind_tools(tools)
    return model