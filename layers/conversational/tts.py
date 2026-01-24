import asyncio
import pyttsx3
import structlog
from interfaces.io import TTSProvider
from core.exceptions import ComponentException, FailureType

logger = structlog.get_logger()

class Pyttsx3TTS(TTSProvider):
    """
    Text-to-Speech implementation using pyttsx3.
    Running in a separate thread to avoid blocking asyncio loop.
    """
    def __init__(self, rate: int = 175, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self._engine = None

    def _init_engine(self):
        """Initialize engine in the worker thread."""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            return engine
        except Exception as e:
            logger.error("Failed to initialize pyttsx3", error=str(e))
            raise ComponentException(f"TTS Init Failed: {e}", FailureType.FATAL)

    def _speak_sync(self, text: str):
        """Synchronous speak function for threading."""
        if not self._engine:
            self._engine = self._init_engine()
        
        try:
            # We must use runAndWait so that it plays. 
            # Note: pyttsx3 event loop behavior can be tricky.
            # Ideally, we create a new engine per utterance or maintain a dedicated thread.
            # Using a simple one-off for now.
            logger.info("Speaking...", text=text)
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            logger.error("TTS failed", error=str(e))
            # On error, try to reset engine
            self._engine = None 
            raise ComponentException(f"TTS Failed: {e}", FailureType.TRANSIENT)

    async def synthesize(self, text: str) -> None:
        """Speak the text."""
        await asyncio.to_thread(self._speak_sync, text)
