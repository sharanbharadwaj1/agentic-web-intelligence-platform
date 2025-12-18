# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Groq settings
    GROQ_API_KEY: str  = "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"                        
    GROQ_API_URL: str = "https://api.groq.ai/openai/v1"   # change if Groq gives a different base
    GROQ_MODEL: str = "llama-3.1-8b-instant"
                     

    # existing/other settings
    GEMINI_API_KEY: str | None = None
    MODEL_NAME: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"

settings = Settings()
