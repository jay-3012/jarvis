import asyncio
import structlog
import speech_recognition as sr
import io
import tempfile
import os
import random
import re

from core.event_bus import internal_bus
from layers.conversational.stt import WhisperSTT
from layers.conversational.tts import Pyttsx3TTS
from layers.intelligence.ollama_llm import OllamaLLM
from layers.skills.app_launcher import AppLauncher
from layers.skills.system_commander import SystemCommander
from layers.skills.git_controller import GitController
from layers.skills.code_assistant import CodeAssistant
from layers.skills.file_searcher import FileSearcher

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
        self.git_controller = GitController()
        self.code_assistant = CodeAssistant()
        self.file_searcher = FileSearcher()
        self.recognizer = sr.Recognizer()
        self.is_running = False
        
        # Adjust for ambient noise
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300  # Default, will adjust

    async def initialize(self):
        """Initialize models and hardware."""
        logger.info("Initializing Voice Manager...")
        await self.stt.initialize()
        
        # Subscribe to file analysis events from UI
        internal_bus.subscribe("analyze_file", self.on_analyze_file)
        
        # Warmup microphone
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise... Please wait.")
            await asyncio.to_thread(self.recognizer.adjust_for_ambient_noise, source, duration=1)
            logger.info("Microphone ready.", energy_threshold=self.recognizer.energy_threshold)

    async def on_analyze_file(self, data: dict):
        """Handle file absorbed from UI."""
        file_path = data.get("path")
        if not file_path or not os.path.exists(file_path):
            return

        logger.info(f"Absorbing file: {file_path}")
        await self.speak(f"Absorbing file {os.path.basename(file_path)}...")
        await internal_bus.publish("status_update", {"status": "thinking"})

        try:
            # For now, assume text/code files
            # TODO: Add logic for images if needed
            if os.path.getsize(file_path) > 100000:
                content = "File too large to read entirely. Reading first 5000 characters."
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content += "\n" + f.read(5000)
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

            prompt = f"I have absorbed a file named '{os.path.basename(file_path)}'. Here is its content:\n\n{content}\n\nPlease analyze this file and tell me what it does or contains."
            
            # Send to LLM
            response = await self.llm.generate_response(prompt)
            
            await self.speak(response)
            await internal_bus.publish("assistant_message", {"text": f"Analysis of {os.path.basename(file_path)}:\n{response}"})

        except Exception as e:
            err_msg = f"Failed to analyze file: {str(e)}"
            logger.error(err_msg)
            await self.speak("I could not analyze that file.")
        
        await internal_bus.publish("status_update", {"status": "idle"})

    async def speak(self, text: str):
        """Output speech."""
        await internal_bus.publish("status_update", {"status": "speaking"})
        await self.tts.synthesize(text)
        await internal_bus.publish("status_update", {"status": "idle"})

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
                await internal_bus.publish("status_update", {"status": "listening"})
                audio_data = await self._listen_one_shot()
                if audio_data:
                     # Thinking/Processing
                     await internal_bus.publish("status_update", {"status": "thinking"})
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

        # Thinking Logic
        await internal_bus.publish("status_update", {"status": "thinking"})
        
        # Send to LLM
        response = await self.llm.generate_response(text)
        
        # Check for commands
        open_match = re.search(r"\[\[OPEN:\s*(.*?)\]\]", response, re.IGNORECASE)
        cmd_match = re.search(r"\[\[CMD:\s*(.*?)\]\]", response, re.IGNORECASE)
        git_match = re.search(r"\[\[GIT:\s*(.*?)\]\]", response, re.IGNORECASE)
        code_match = re.search(r"\[\[CODE:\s*(.*?)\]\]", response, re.IGNORECASE)
        search_match = re.search(r"\[\[SEARCH:\s*(.*?)\]\]", response, re.IGNORECASE)
        
        if open_match:
            app_name = open_match.group(1)
            logger.info(f"Detected OPEN command: {app_name}")
            result = await self.app_launcher.execute({"app_name": app_name})
            await self.speak(result)
            await internal_bus.publish("assistant_message", {"text": f"Opened {app_name}"})
            
        elif cmd_match:
            command = cmd_match.group(1)
            logger.info(f"Detected CMD command: {command}")
            await self.speak(f"Executing system command: {command}")
            result = await self.system_commander.execute({"command": command})
            await self.speak(result)
            await internal_bus.publish("assistant_message", {"text": f"Executed: {command}"})

        elif git_match:
            command = git_match.group(1)
            logger.info(f"Detected GIT command: {command}")
            await self.speak("Executing Git command...")
            result = await self.git_controller.execute({"command": command})
            await self.speak(result)
            await internal_bus.publish("assistant_message", {"text": f"Git: {command}"})

        elif code_match:
            command = code_match.group(1)
            logger.info(f"Detected CODE command: {command}")
            # Do not announce always if it's just reading, but maybe briefly
            result = await self.code_assistant.execute({"command": command})
            await self.speak(result)
            await internal_bus.publish("assistant_message", {"text": f"Code Operation Complete"})

        elif search_match:
            command = search_match.group(1)
            logger.info(f"Detected SEARCH command: {command}")
            await self.speak("Searching for files...")
            result = await self.file_searcher.execute({"command": command})
            await self.speak(result)
            await internal_bus.publish("assistant_message", {"text": f"Search Results: {result}"})
            
        else:
            # Just speak response
            await self.speak(response)
            await internal_bus.publish("assistant_message", {"text": response})

        # Back into listening handled by loop, but we can set status to idle briefly
        await internal_bus.publish("status_update", {"status": "idle"})

    def stop(self):
        self.is_running = False
