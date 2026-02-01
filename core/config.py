import os
from typing import List, Optional, Union
from pydantic import Field, AnyHttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Global configuration settings for Jarvis.
    Loads from environment variables.
    """
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        extra='ignore',  # Safer for now, avoids crashing on new/unknown env vars
        case_sensitive=False
    )

    # ===== Application Settings =====
    APP_NAME: str = "Jarvis"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ===== Security =====
    SECRET_KEY: str = "your-secret-key-change-this-to-a-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 720

    # ===== Database Configuration =====
    # Handling potential validation issues with DSNs by allowing str
    DATABASE_URL: str = "postgresql://jarvis:jarvis_password@localhost:5432/jarvis"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ===== Redis Configuration =====
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 50
    USE_INTERNAL_BUS: bool = True

    # ===== Ollama Configuration =====
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2:1b"
    OLLAMA_TIMEOUT: int = 60
    
    # Alias for LLM usage
    LLM_MODEL: str = Field(alias="OLLAMA_DEFAULT_MODEL", default="llama3.2:1b")

    # ===== ChromaDB Configuration =====
    CHROMADB_URL: str = "http://localhost:8002"
    CHROMADB_COLLECTION: str = "jarvis_files"

    # ===== Central Server =====
    CENTRAL_SERVER_HOST: str = "0.0.0.0"
    CENTRAL_SERVER_PORT: int = 8000
    WEBSOCKET_PORT: int = 8001

    # ===== Device Configuration =====
    DEVICE_ID: str = "windows-laptop"
    DEVICE_TYPE: str = "desktop"
    DEVICE_NAME: str = "Windows Laptop"
    IS_CENTRAL_DEVICE: bool = False
    CENTRAL_DEVICE_ID: str = "central-hub"

    # ===== Voice Configuration =====
    STT_MODEL_PATH: str = "./models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20"
    TTS_MODEL_PATH: str = "./models/en_US-lessac-medium.onnx"
    VOICE_SAMPLE_RATE: int = 16000
    STT_MODEL: str = "base" # Legacy field

    # ===== File Indexing =====
    FILE_INDEX_ENABLED: bool = True
    FILE_INDEX_INTERVAL: int = 300
    FILE_INDEX_EXCLUDE_PATTERNS: str = "node_modules,venv,.git,__pycache__"

    # ===== Monitoring =====
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # ===== CORS Settings =====
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    CORS_ALLOW_CREDENTIALS: bool = True

    # ===== Task Queue =====
    TASK_QUEUE_NAME: str = "jarvis_tasks"
    TASK_QUEUE_MAX_RETRIES: int = 3
    TASK_QUEUE_RETRY_DELAY: int = 5

    # ===== Logging =====
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/jarvis.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # ===== Prompts =====
    # Keeping the prompt in the code as it's large/complex, or load from file/env if needed
    SYSTEM_PROMPT: str = (
        "You are Jarvis, a highly intelligent and helpful AI assistant. "
        "Keep your answers concise and human-like. "
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

global_settings = Settings()
