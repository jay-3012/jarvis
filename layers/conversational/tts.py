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
            
            # Select Voice based on Config
            voices = engine.getProperty('voices')
            selected_voice = None
            
            # 1. Try specific VOICE_ID from config
            if global_settings.VOICE_ID:
                for v in voices:
                    if v.id == global_settings.VOICE_ID:
                        selected_voice = v.id
                        break
            
            # 2. Try matching LANGUAGE from config (e.g., 'hi' for Hindi)
            if not selected_voice and global_settings.LANGUAGE:
                search_term = "hindi" if global_settings.LANGUAGE == "hi" else global_settings.LANGUAGE
                for v in voices:
                    # Check name and languages list
                    if search_term.lower() in v.name.lower():
                        selected_voice = v.id
                        break
                        
                    # Check v.languages if it exists (it's a list)
                    try:
                        for lang in v.languages:
                            if search_term.lower() in str(lang).lower():
                                selected_voice = v.id
                                break
                    except: 
                        pass
                    if selected_voice: break

            if selected_voice:
                engine.setProperty('voice', selected_voice)
                logger.info("TTS Voice Set", voice=selected_voice)
            else:
                logger.warning("Requested voice not found, using default.")

            return engine
        except Exception as e:
            logger.error("Failed to initialize pyttsx3", error=str(e))
            raise ComponentException(f"TTS Init Failed: {e}", FailureType.FATAL)

    def _speak_sync(self, text: str):
        """Synchronous speak function for threading."""
        engine = None
        try:
            # Re-initialize engine every time to avoid loop conflicts in threaded env
            engine = self._init_engine()
            logger.info("Speaking...", text=text[:50]) # Log first 50 chars
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error("TTS failed", error=str(e))
            raise ComponentException(f"TTS Failed: {e}", FailureType.TRANSIENT)
        finally:
            if engine:
                try:
                    engine.stop()
                    del engine
                except Exception:
                    pass

    async def synthesize(self, text: str) -> None:
        """Speak the text."""
        await asyncio.to_thread(self._speak_sync, text)
