import os
import sherpa_onnx
import sounddevice as sd
import numpy as np
import structlog
from typing import Optional
from interfaces.io import TTSProvider
from core.config import global_settings
from core.exceptions import ComponentException, FailureType

logger = structlog.get_logger()

class SherpaTTS(TTSProvider):
    """
    Offline Neural TTS using Sherpa-ONNX.
    Uses VITS models.
    """
    def __init__(self):
        self.model_path = os.path.join(os.getcwd(), "assets", "models", "vits-mms-hin")
        self.tts = None
        self.sample_rate = 16000 # Default for MMS

    def initialize(self):
        """Load the model."""
        if self.tts:
            return

        model_file = os.path.join(self.model_path, "model.onnx")
        tokens_file = os.path.join(self.model_path, "tokens.txt")

        if not os.path.exists(model_file) or not os.path.exists(tokens_file):
            raise ComponentException("Sherpa Model not found. Run utils/setup_sherpa.py", FailureType.FATAL)

        logger.info("Loading Sherpa-ONNX Model...", path=self.model_path)
        try:
            config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=model_file,
                        lexicon="",
                        tokens=tokens_file,
                    ),
                    provider="cpu",
                    debug=False,
                    num_threads=2,
                )
            )
            self.tts = sherpa_onnx.OfflineTts(config)
            self.sample_rate = self.tts.sample_rate
            logger.info("Sherpa-ONNX Loaded", sample_rate=self.sample_rate)
        except Exception as e:
            logger.error("Failed to load Sherpa-ONNX", error=str(e))
            raise ComponentException(f"Sherpa Init Failed: {e}", FailureType.FATAL)

    async def synthesize(self, text: str):
        """Generate and play audio."""
        if not self.tts:
            self.initialize()

        logger.info("Generatng Audio (Sherpa)...", text=text[:50])
        try:
            audio = self.tts.generate(text, sid=0, speed=1.0)
            
            # Play audio using sounddevice
            # audio.samples is a numpy array of float32
            sd.play(audio.samples, self.sample_rate)
            sd.wait()
            
        except Exception as e:
            logger.error("Sherpa TTS Failed", error=str(e))
            raise ComponentException(f"Sherpa TTS Failed: {e}", FailureType.TRANSIENT)
