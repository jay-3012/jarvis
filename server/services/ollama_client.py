"""Ollama LLM service client."""

import httpx
import structlog
import os
from typing import Optional, Dict, Any

logger = structlog.get_logger()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))


def check_ollama_connection() -> bool:
    """Check if Ollama service is available."""
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        logger.debug("Ollama connection check failed", error=str(e))
        return False


def generate(prompt: str, model: str = "llama3.2:1b", **kwargs) -> Optional[str]:
    """
    Generate text using Ollama.
    
    Args:
        prompt: Input prompt
        model: Model name (default: llama3.2:1b)
        **kwargs: Additional parameters for Ollama API
        
    Returns:
        Generated text or None if failed
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json().get("response")
        else:
            logger.error("Ollama generation failed", status=response.status_code, response=response.text)
            return None
            
    except Exception as e:
        logger.error("Ollama generation error", error=str(e))
        return None


def list_models() -> list:
    """List available Ollama models."""
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        if response.status_code == 200:
            return response.json().get("models", [])
        return []
    except Exception as e:
        logger.error("Failed to list Ollama models", error=str(e))
        return []
