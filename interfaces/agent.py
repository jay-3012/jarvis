from typing import Protocol, Any, Dict, Optional
from abc import abstractmethod

class Agent(Protocol):
    """
    Protocol definition for a generic Agent.
    Agents observe, plan, and act.
    """
    @property
    def name(self) -> str:
        """The unique name of the agent."""
        ...

    async def initialize(self) -> None:
        """Perform any necessary startup logic."""
        ...

    async def process(self, input_data: Any) -> Any:
        """Process input and return a result."""
        ...
    
    async def shutdown(self) -> None:
        """Cleanup resources."""
        ...

class Executor(Protocol):
    """
    Protocol for components that execute concrete actions.
    Executors should be stateless and task-bound.
    """
    @property
    def executor_id(self) -> str:
        ...

    async def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task.
        Must return a dictionary containing the result status and data.
        """
        ...
