import asyncio
import structlog
import speech_recognition as sr
from typing import AsyncGenerator
import io
import tempfile
import os

from core.event_bus import internal_bus
from layers.conversational.stt import WhisperSTT
from layers.conversational.tts import Pyttsx3TTS

logger = structlog.get_logger()

class VoiceManager:
    """
    Manages the voice interaction loop:
    Listen (Microphone) -> Detect (VAD/Wake) -> Transcribe (STT) -> Speak (TTS)
    """
    def __init__(self):
        self.stt = WhisperSTT()
        self.tts = Pyttsx3TTS()
        self.recognizer = sr.Recognizer()
        self.is_running = False
        
        # Adjust for ambient noise
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300  # Default, will adjust

    async def initialize(self):
        """Initialize models and hardware."""
        logger.info("Initializing Voice Manager...")
        await self.stt.initialize()
        # TTS inits lazily
        
        # Warmup microphone
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise... Please wait.")
            await asyncio.to_thread(self.recognizer.adjust_for_ambient_noise, source, duration=1)
            logger.info("Microphone ready.", energy_threshold=self.recognizer.energy_threshold)

    async def speak(self, text: str):
        """Output speech."""
        await self.tts.synthesize(text)

    async def listen_loop(self):
        """
        Continuous listening loop.
        1. Listen for audio segment.
        2. Transcribe.
        3. Publish 'user_message' event.
        """
        self.is_running = True
        logger.info("Starting listening loop...")
        
        while self.is_running:
            try:
                audio_data = await self._listen_one_shot()
                if audio_data:
                     # Save temporarily to disk for Whisper (easier than in-memory for now)
                     # faster-whisper accepts file paths.
                     text = await self._process_audio(audio_data)
                     
                     if text:
                         # Publish event
                         await internal_bus.publish("user_message", {"text": text, "source": "voice"})
                         
                         # For now, immediate echo for implementing the loop
                         await self._handle_echo(text)

            except Exception as e:
                logger.error("Error in listening loop", error=str(e))
                await asyncio.sleep(1)

    async def _listen_one_shot(self) -> sr.AudioData:
        """Capture one phrase."""
        loop = asyncio.get_event_loop()
        with sr.Microphone() as source:
            logger.debug("Listening...")
            # We use a shorter timeout to allow checking is_running
            try:
                # running listen in thread to avoid blocking main loop
                audio = await loop.run_in_executor(None, lambda: self.recognizer.listen(source, timeout=1, phrase_time_limit=10))
                return audio
            except sr.WaitTimeoutError:
                return None

    async def _process_audio(self, audio: sr.AudioData) -> str:
        """Process raw audio to text."""
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio.get_wav_data())
            tmp_path = tmp.name
        
        try:
            text = await self.stt.transcribe(tmp_path)
            return text
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def _handle_echo(self, text: str):
        """Temporary handler: Echo back."""
        if not text:
            return
        logger.info(f"User said: {text}")
        
        # Simple Logic to test
        if "hello" in text.lower():
            await self.speak("Hello there! System is online.")
        elif "stop" in text.lower():
            await self.speak("Stopping voice loop.")
            self.stop()
        else:
            await self.speak(f"I heard: {text}")

    def stop(self):
        self.is_running = False
