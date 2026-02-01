import structlog
from typing import Dict, Any, List

from layers.cognitive.memory import SemanticMemory
from layers.cognitive.planner import CognitivePlanner
from layers.cognitive.reflector import Reflector
from server.services.llm_service import llm_service

logger = structlog.get_logger()

class MetaAgent:
    """
    The orchestrator of the Cognitive Layer.
    Coordinates Memory, Planning, and Reflection.
    """
    
    def __init__(self):
        self.memory = SemanticMemory()
        self.planner = CognitivePlanner(llm_service)
        self.reflector = Reflector(llm_service)
        
    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user request through the cognitive loop.
        
        Returns:
            Dict containing the 'response' text and 'plan' data.
        """
        logger.info("MetaAgent processing request", user_input=user_input)
        
        # 1. Recall (Memory)
        # Search for relevant context
        context_results = self.memory.query_context(user_input, n_results=2)
        context_strs = [res['text'] for res in context_results]
        
        # 2. Plan
        # Generate a multi-step plan
        plan = await self.planner.create_plan(user_input, context=context_strs)
        
        # 3. Reflect
        # Check if the plan is safe
        is_safe, feedback = await self.reflector.review_plan(user_input, plan)
        
        if not is_safe:
            return {
                "text": f"I cannot execute that plan. Safety check failed: {feedback}",
                "plan": [],
                "status": "rejected"
            }
            
        # 4. Save to Memory (Episodic)
        self.memory.save_context(f"User: {user_input}", metadata={"type": "conversation", "role": "user"})
        
        # 5. Execute / Response
        # For now, we return the plan. The ConversationManager will handle execution loop.
        # In the future, the MetaAgent might own the execution loop.
        
        return {
            "text": f"I have created a plan with {len(plan)} steps.",
            "plan": plan,
            "status": "planned"
        }

# Global instance
meta_agent = MetaAgent()
