import structlog
from typing import List, Dict, Any, Tuple

logger = structlog.get_logger()

class Reflector:
    """
    Critiques plans for safety, feasibility, and correctness.
    """
    
    def __init__(self, llm_service):
        self.llm = llm_service

    async def review_plan(self, goal: str, plan: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Review a proposed plan.
        
        Returns:
            (is_approved: bool, feedback: str)
        """
        plan_str = str(plan)
        prompt = f"""You are the Safety Officer (Reflector) for an AI agent.
Review the following plan for the USER GOAL.

USER GOAL: "{goal}"

PROPOSED PLAN:
{plan_str}

Check for:
1. Safety: Are there dangerous commands (delete all files, format drive)?
2. Feasibility: Do the steps logically follow each other?
3. Redundancy: Are there unnecessary steps?

If the plan is safe and good, respond with "APPROVED".
If not, respond with "REJECTED: <reason>".

RESPONSE:"""

        try:
            response = await self.llm.generate_response(prompt, model="llama3.2:1b") # Fast model for check
            if not response:
                return True, "No response from reflector, proceeding with caution."
            
            response = response.strip()
            if "APPROVED" in response.upper():
                logger.info("Plan approved by Reflector")
                return True, "Approved"
            else:
                logger.warning("Plan rejected by Reflector", feedback=response)
                return False, response
                
        except Exception as e:
            logger.error("Reflection failed", error=str(e))
            return True, "Reflection error, proceeding." # Fail open or closed? Fail open for now for prototype.
