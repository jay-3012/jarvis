"""LLM service for conversation management and intent parsing."""

import structlog
from typing import Optional, Dict, Any
from server.services.ollama_client import generate

logger = structlog.get_logger()


class LLMService:
    """LLM service with dynamic model switching."""
    
    def __init__(self):
        self.default_model = "llama3.2:1b"
        self.models = {
            "fast": "llama3.2:1b",      # Simple commands, classification
            "balanced": "llama3.2:3b",   # General dialogue (if available)
            "advanced": "llama3.1:8b"    # Complex tasks (if available)
        }
    
    def select_model(self, complexity: str = "fast") -> str:
        """Select model based on task complexity."""
        return self.models.get(complexity, self.default_model)
    
    async def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user intent from natural language input.
        
        Returns:
            dict with 'intent', 'action', 'params'
        """
        prompt = f"""Parse the following user command and extract the intent, action, and parameters.
Respond in JSON format with keys: intent, action, params.

User command: "{user_input}"

JSON response:"""
        
        try:
            response = generate(prompt, model=self.default_model)
            if response:
                # Try to parse JSON from response
                import json
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response.strip()
                
                result = json.loads(json_str)
                logger.info("Intent parsed", intent=result.get("intent"))
                return result
            else:
                logger.warning("No response from LLM")
                return {"intent": "unknown", "action": "none", "params": {}}
                
        except Exception as e:
            logger.error("Intent parsing failed", error=str(e))
            return {"intent": "error", "action": "none", "params": {}}
    
    async def generate_response(self, prompt: str, model: str = None) -> Optional[str]:
        """Generate a text response using the LLM."""
        model = model or self.default_model
        try:
            response = generate(prompt, model=model)
            return response
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return None
    
    async def chat(self, messages: list, model: str = None) -> Optional[str]:
        """
        Chat with the LLM using conversation history.
        
        Args:
            messages: List of {role: str, content: str} messages
            model: Model to use (optional)
        """
        model = model or self.default_model
        
        # Format messages into a prompt
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
            elif role == "system":
                prompt += f"System: {content}\n"
        
        prompt += "Assistant: "
        
        try:
            response = generate(prompt, model=model)
            return response
        except Exception as e:
            logger.error("Chat failed", error=str(e))
            return None


# Global LLM service instance
llm_service = LLMService()
