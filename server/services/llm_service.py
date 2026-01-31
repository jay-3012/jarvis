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
        
        Supported Intents:
        - get_online_devices: Query about connected/active devices
        - file_search: Search for a file (params: filename, device_name)
        - command_execution: General command execution
        
        Returns:
            dict with 'intent', 'action', 'params'
        """
        prompt = f"""You are the intent parser for the Jarvis system.
Analyze the following User Command and extract the intent, specific action, and parameters.

Supported Intents:
1. get_online_devices
   - Triggers: "which devices are online", "status report", "who is connected"
   - Action: "list_devices"
   - Params: None

2. file_search
   - Triggers: "search for file.txt", "find report.pdf on mac", "where is my photo"
   - Action: "search_file"
   - Params: 
     - filename (string): The name of the file
     - device (string, optional): The target device name (e.g., "mac", "windows", "iphone")

3. command_execution
   - Triggers: "open chrome", "say hello"
   - Action: <specific_action>
   - Params: <action_params>

Response Format (JSON only):
{{
  "intent": "<intent_name>",
  "action": "<action_name>",
  "params": {{ <extracted_parameters> }}
}}

User Command: "{user_input}"

JSON Response:"""
        
        try:
            response = await self.generate_response(prompt, model=self.default_model)
            if response:
                # Try to parse JSON from response
                import json
                # Extract JSON from response (handle markdown code blocks)
                json_str = response
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
