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
    SYSTEM_PROMPT: str = (
        "You are Jarvis, a highly intelligent and helpful AI assistant. "
        "Keep your answers concise and human-like. "
        "Do not use markdown formatting like bold or headers in your speech. "
        "TOOLS: "
        "1. Open Apps: [[OPEN: app_name]]. Example: 'Open Notepad' -> '[[OPEN: notepad]]'. "
        "2. Run Commands: [[CMD: command_line]]. Example: 'Create folder Work' -> '[[CMD: mkdir Work]]'. "
        "Otherwise, reply normally."
    )
    STT_MODEL: str = "base"
    
global_settings = Settings()
