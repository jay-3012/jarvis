"""Conversation manager for handling natural language interactions."""

import structlog
from typing import Dict, Any, Optional
from server.websocket import manager
from server.websocket.protocol import CommandMessage
import uuid
import json

logger = structlog.get_logger()

class ConversationManager:
    """
    Orchestrates the conversation flow:
    User Input -> Meta Agent (Cognitive Layer) -> Response/Plan -> Execution
    """
    
    async def process_input(self, user_input: str, user_id: str = None) -> Dict[str, Any]:
        """Process user text input and return a response."""
        
        # Lazy import to avoid circular dependencies and wait for initialization
        from layers.cognitive.meta_agent import meta_agent
        
        logger.info("Processing input via Cognitive Layer", user_input=user_input)
        
        # Delegate to MetaAgent
        result = await meta_agent.process_request(user_input)
        
        response_text = result.get("text")
        plan = result.get("plan", [])
        status = result.get("status")
        
        # If there is a plan, we currently just return it to the user.
        # Future: Execute the plan automatically.
        
        data = {
            "plan": plan,
            "status": status
        }
        
        return {
            "text": response_text,
            "intent": "cognitive_execution",
            "data": data
        }

# Global instance
conversation_manager = ConversationManager()
