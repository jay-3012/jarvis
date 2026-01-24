import structlog
import ollama
from interfaces.llm_provider import LLMProvider
from core.config import global_settings
from core.exceptions import ComponentException, FailureType

logger = structlog.get_logger()

class OllamaLLM(LLMProvider):
    """
    LLM Provider using local Ollama instance.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or global_settings.LLM_MODEL
        self.history = [] # List of {'role': str, 'content': str}
        logger.info("Initialized OllamaLLM", model=self.model_name)

    async def generate_response(self, prompt: str) -> str:
        """
        Generate response using Ollama library with history.
        """
        logger.info("Sending prompt to LLM...", prompt_preview=prompt[:50])
        
        # 1. Add user message to history
        self.history.append({'role': 'user', 'content': prompt})
        
        # 2. Prepare payload (System Prompt + History)
        messages = [{'role': 'system', 'content': global_settings.SYSTEM_PROMPT}] + self.history

        try:
            # ollama.chat is synchronous
            import asyncio
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model_name,
                messages=messages
            )
            
            content = response['message']['content']
            
            # 3. Add assistant response to history
            self.history.append({'role': 'assistant', 'content': content})
            
            # 4. Limit history to last 20 messages to keep context efficient
            if len(self.history) > 20:
                self.history = self.history[-20:]
                
            logger.info("LLM Response received", length=len(content))
            return content
            
        except Exception as e:
            logger.error("LLM Generation Failed", error=str(e))
            raise ComponentException(f"Ollama generation failed: {e}", FailureType.TRANSIENT)
