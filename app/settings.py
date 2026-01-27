import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """
    Application settings.
    """
    # General
    APP_NAME: str = "Gene-to-Protein Portal"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API
    API_PREFIX: str = ""
    G2P_PORTAL_API_URL: str = os.getenv("G2P_PORTAL_API_URL", "https://g2p.broadinstitute.org/api")
    G2P_PORTAL_API_KEY: str = os.getenv("G2P_PORTAL_API_KEY", "")
    
    # Model / AI
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GOOGLE_GEMINI_MODEL: str = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.5-pro")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")

settings = Settings()
