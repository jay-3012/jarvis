from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers (e.g., Ollama, OpenCV, OpenAI).
    """

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a text response for the given prompt.
        """
        pass
