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
        "Reply in the language matching the user's input or the system language (Hindi/English). "
        "Do not use markdown formatting like bold or headers in your speech. "
        "TOOLS: "
        "1. Open Apps: [[OPEN: app_name]]. "
        "2. Run Commands: [[CMD: command]]. "
        "3. Git Control: [[GIT: command]]. Example: 'Commit changes' -> '[[GIT: commit -m \"update\"]]'. "
        "4. Code Ops: [[CODE: action args]]. Example: 'Read main.py' -> '[[CODE: read main.py]]'. "
        "5. File Search: [[SEARCH: pattern path]]. Example: 'Find PDF in docs' -> '[[SEARCH: *.pdf C:/Users/vishw/Documents]]'. "
        "6. Todo List: [[TODO: task_content]]. Example: 'Remind me to buy milk' -> '[[TODO: Buy milk]]'. "
        "Otherwise, reply normally."
    )
    STT_MODEL: str = "base"
    LANGUAGE: str = "hi"
    VOICE_ID: str = "" # Optional: Specific voice ID
    TTS_ENGINE: str = "offline_neural" # offline_os, offline_neural, online
    
global_settings = Settings()
