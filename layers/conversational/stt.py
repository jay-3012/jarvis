import asyncio
import structlog
from typing import Any
from faster_whisper import WhisperModel
from interfaces.io import STTProvider
from core.config import global_settings
from core.exceptions import ComponentException, FailureType

logger = structlog.get_logger()

class WhisperSTT(STTProvider):
    """
    Speech-to-Text implementation using faster-whisper.
    """
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Lazy load the model."""
        if self._model:
            return

        logger.info("Loading Whisper model...", size=self.model_size, device=self.device)
        try:
            # Running model loading in a separate thread to not block the event loop
            self._model = await asyncio.to_thread(
                WhisperModel, 
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type
            )
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error("Failed to load Whisper model", error=str(e))
            raise ComponentException(f"STT Model Load Failed: {e}", FailureType.FATAL)

    async def transcribe(self, audio_data: Any, language: str = None) -> str:
        """
        Transcribe audio data (bytes or path).
        For SpeechRecognition AudioData, we might need to process it.
        We expect audio_path for now or raw bytes if supported.
        """
        if not self._model:
             await self.initialize()

        logger.info("Transcribing audio...", language=language)
        try:
            # We assume audio_data is a file path or a binary stream acceptable by transcribe
            # faster-whisper accepts: file-like object, numpy array, or path
            
            segments, info = await asyncio.to_thread(
                self._model.transcribe, 
                audio_data, 
                beam_size=5,
                language=language # Pass language constraint
            )
            
            text = " ".join([segment.text for segment in segments])
            text = text.strip()
            
            logger.info("Transcription complete", text=text, language=info.language, probability=info.language_probability)
            return text
            
        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            raise ComponentException(f"Transcription failed: {str(e)}", FailureType.TRANSIENT)
