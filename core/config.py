import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Global configuration settings for Jarvis.
    Loads from environment variables.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # General
    APP_NAME: str = "Jarvis"
    DEBUG: bool = False
    
    # Event Bus
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_INTERNAL_BUS: bool = True  # Default to internal bus for development

    # Providers
    LLM_MODEL: str = "llama3.2:3b"
    STT_MODEL: str = "base"
    
global_settings = Settings()
