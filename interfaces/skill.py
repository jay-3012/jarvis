from abc import ABC, abstractmethod
from typing import Any, Dict

class Skill(ABC):
    """
    Abstract Base Class for Jarvis Skills.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the skill."""
        pass

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> str:
        """
        Execute the skill with the given parameters.
        Returns a success message or result string.
        """
        pass
