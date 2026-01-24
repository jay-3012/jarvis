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
from layers.intelligence.ollama_llm import OllamaLLM
from layers.skills.app_launcher import AppLauncher
from layers.skills.system_commander import SystemCommander
import random
import re

logger = structlog.get_logger()

class VoiceManager:
    """
    Manages the voice interaction loop:
    Listen (Microphone) -> Detect (VAD/Wake) -> Transcribe (STT) -> Speak (TTS)
    """
    def __init__(self):
        self.stt = WhisperSTT()
        self.tts = Pyttsx3TTS()
        self.llm = OllamaLLM()
        self.app_launcher = AppLauncher()
        self.system_commander = SystemCommander()
        self.recognizer = sr.Recognizer()
        self.is_running = False
        
        # Adjust for ambient noise
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300  # Default, will adjust

    async def initialize(self):
        """Initialize models and hardware."""
        logger.info("Initializing Voice Manager...")
        await self.stt.initialize()
        # TTS and LLM init lazily or contain lightweight init logic
        
        # Warmup microphone
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise... Please wait.")
            await asyncio.to_thread(self.recognizer.adjust_for_ambient_noise, source, duration=1)
            logger.info("Microphone ready.", energy_threshold=self.recognizer.energy_threshold)

    async def speak(self, text: str):
        """Output speech."""
        await self.tts.synthesize(text)

    async def _play_listening_cue(self):
        """Verbal cue to indicate listen state."""
        # We can add variety here to make it more natural
        prompts = [
            "I am waiting for your command.",
            "Listening.",
            "Go ahead.",
            "Status ready. Waiting for input."
        ]
        await self.speak(random.choice(prompts))

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
                await self._play_listening_cue()
                audio_data = await self._listen_one_shot()
                if audio_data:
                     # Save temporarily to disk for Whisper (easier than in-memory for now)
                     # faster-whisper accepts file paths.
                     text = await self._process_audio(audio_data)
                     
                     if text:
                         # Publish event
                         await internal_bus.publish("user_message", {"text": text, "source": "voice"})
                         
                         await self._handle_conversation(text)

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
                # timeout=8: Wait 8 seconds for speech. If silence, loop repeats and speaks cue again.
                audio = await loop.run_in_executor(None, lambda: self.recognizer.listen(source, timeout=8, phrase_time_limit=10))
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

    async def _handle_conversation(self, text: str):
        """Handle inputs with LLM and Skills."""
        if not text:
            return
        logger.info(f"User said: {text}")
        
        # Hardcoded commands for control
        if "stop voice" in text.lower() or "shutdown system" in text.lower():
            await self.speak("Shutting down voice loop.")
            self.stop()
            return

        # Send to LLM
        response = await self.llm.generate_response(text)
        
        # Check for commands
        open_match = re.search(r"\[\[OPEN:\s*(.*?)\]\]", response, re.IGNORECASE)
        cmd_match = re.search(r"\[\[CMD:\s*(.*?)\]\]", response, re.IGNORECASE)
        
        if open_match:
            app_name = open_match.group(1)
            logger.info(f"Detected OPEN command: {app_name}")
            result = await self.app_launcher.execute({"app_name": app_name})
            await self.speak(result)
            
        elif cmd_match:
            command = cmd_match.group(1)
            logger.info(f"Detected CMD command: {command}")
            # Announce intent before executing dangerous commands
            await self.speak(f"Executing system command: {command}")
            result = await self.system_commander.execute({"command": command})
            await self.speak(result)
            
        else:
            # Just speak response
            await self.speak(response)

    def stop(self):
        self.is_running = False
