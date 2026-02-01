import structlog
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = structlog.get_logger()

class PlanStep(BaseModel):
    step_id: int
    description: str
    tool: str
    params: Dict[str, Any]
    dependencies: List[int] = []

class CognitivePlanner:
    """
    Decomposes high-level goals into executable steps (DAG).
    """
    
    def __init__(self, llm_service):
        self.llm = llm_service

    async def create_plan(self, goal: str, context: List[str] = []) -> List[Dict[str, Any]]:
        """
        Generate a plan for a specific goal.
        
        Args:
            goal: The user's high-level request.
            context: Relevant context strings from memory.
            
        Returns:
            List of steps (dicts).
        """
        context_str = "\n".join(context)
        prompt = f"""You are the Planner for an advanced AI agent.
Your task is to break down the USER GOAL into a list of executable steps.

Available Tools:
- search_file(filename, device)
- list_devices()
- run_command(command, background=False)
- open_app(app_name)
- read_file(path)
- web_search(query)

USER GOAL: "{goal}"

CONTEXT:
{context_str}

Return a JSON list of steps. Each step must have:
- id: integer (1-based)
- description: string
- tool: string (from available tools, or "thought" if no tool needed)
- params: dict (arguments for the tool)
- dependencies: list of IDs that must complete before this step

Example JSON:
[
  {{
    "id": 1,
    "description": "Find the file",
    "tool": "search_file",
    "params": {{"filename": "report.pdf"}},
    "dependencies": []
  }},
  {{
    "id": 2,
    "description": "Email it (mock)",
    "tool": "run_command",
    "params": {{"command": "echo 'sending email'"}},
    "dependencies": [1]
  }}
]

JSON RESPONSE:"""

        try:
            response = await self.llm.generate_response(prompt, model="llama3.2:3b") # Use smarter model for planning
            if not response:
                return []
                
            # Parse JSON
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            
            steps = json.loads(json_str)
            logger.info("Plan created", steps_count=len(steps))
            return steps
            
        except Exception as e:
            logger.error("Planning failed", error=str(e))
            return []
