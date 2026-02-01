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
        
        # 0. Quick Intent Check (Implicit)
        # Is this a question about the project?
        is_project_query = any(keyword in user_input.lower() for keyword in 
                             ['how', 'explain', 'where is', 'what is', 'code', 'file', 'architecture'])
        
        # 1. Recall (Memory)
        # Search for relevant context
        # If it looks like a deep question, get more context
        n_results = 5 if is_project_query else 2
        context_results = self.memory.query_context(user_input, n_results=n_results)
        
        # Format context for LLM
        context_strs = []
        for res in context_results:
             source = res.get('metadata', {}).get('file_path', 'unknown')
             text = res.get('text', '')
             context_strs.append(f"Source: {source}\nContent:\n{text}")
        
        # 2. Plan / Answer
        # If it's a direct question, we might not need a "plan" but an "answer".
        # For now, let's treat everything as a Planning problem where the plan might be "Answer the user".
        
        # However, if the user asks "Explain X", the Planner might be overkill.
        # Let's add a direct answering capability if the Plan returns empty or "Thought".
        
        plan = await self.planner.create_plan(user_input, context=context_strs)
        
        # Check if the plan is just a thought or empty
        # If it's a pure question (no actions needed), the planner might return nothing relevant.
        # In that case, generate a direct answer using RAG.
        if not plan or (len(plan) == 1 and plan[0].get('tool') == 'thought'):
             answer = await llm_service.chat([
                 {"role": "system", "content": f"You are an expert on this project. Context:\n{chr(10).join(context_strs)}"},
                 {"role": "user", "content": user_input}
             ])
             return {
                 "text": answer,
                 "plan": [],
                 "status": "answered"
             }
        
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
        
        return {
            "text": f"I have created a plan with {len(plan)} steps.",
            "plan": plan,
            "status": "planned"
        }

# Global instance
meta_agent = MetaAgent()
