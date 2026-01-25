# layers/conversational/voice_manager.py (REFACTORED)

import asyncio
import structlog
import speech_recognition as sr
import tempfile
import os

from core.event_bus import internal_bus
from layers.conversational.stt import WhisperSTT
from layers.conversational.tts import Pyttsx3TTS
from layers.dialogue.manager import DialogueManager, ResponseType  # NEW
from layers.skills.app_launcher import AppLauncher
from layers.skills.system_commander import SystemCommander
from layers.skills.git_controller import GitController
from layers.skills.code_assistant import CodeAssistant
from layers.skills.file_searcher import FileSearcher

logger = structlog.get_logger()

class VoiceManager:
    """
    Manages the voice interaction loop:
    Listen (Microphone) -> Transcribe (STT) -> DialogueManager -> Execute -> Speak (TTS)
    
    REFACTORED: Now delegates conversational logic to DialogueManager
    """
    def __init__(self):
        self.stt = WhisperSTT()
        self.tts = Pyttsx3TTS()
        self.dialogue_manager = DialogueManager()  # NEW: Dialogue logic separated
        
        # Skills
        self.skills = {
            'OPEN': AppLauncher(),
            'CMD': SystemCommander(),
            'GIT': GitController(),
            'CODE': CodeAssistant(),
            'SEARCH': FileSearcher(),
        }
        
        self.recognizer = sr.Recognizer()
        self.is_running = False
        
        # Adjust for ambient noise
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300

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
            # Read file content
            if os.path.getsize(file_path) > 100000:
                content = "File too large to read entirely. Reading first 5000 characters."
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content += "\n" + f.read(5000)
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

            prompt = f"I have absorbed a file named '{os.path.basename(file_path)}'. Here is its content:\n\n{content}\n\nPlease analyze this file and tell me what it does or contains."
            
            # Use DialogueManager
            response_data = await self.dialogue_manager.process_user_input(prompt)
            
            await self.speak(response_data['text'])
            await internal_bus.publish("assistant_message", {
                "text": f"Analysis of {os.path.basename(file_path)}:\n{response_data['text']}"
            })

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

    async def listen_loop(self):
        """
        Continuous listening loop.
        1. Listen for audio segment.
        2. Transcribe.
        3. Process with DialogueManager.
        4. Execute tools or speak response.
        """
        self.is_running = True
        logger.info("Starting listening loop...")
        
        # Initial greeting
        await self.speak("Jarvis online. How can I help?")
        
        while self.is_running:
            try:
                await internal_bus.publish("status_update", {"status": "listening"})
                audio_data = await self._listen_one_shot()
                
                if audio_data:
                    # Thinking/Processing
                    await internal_bus.publish("status_update", {"status": "thinking"})
                    text = await self._process_audio(audio_data)
                    
                    if text:
                        # Publish user message
                        await internal_bus.publish("user_message", {"text": text, "source": "voice"})
                        
                        # Process with DialogueManager
                        await self._handle_conversation(text)

            except Exception as e:
                logger.error("Error in listening loop", error=str(e))
                await asyncio.sleep(1)

    async def _listen_one_shot(self) -> sr.AudioData:
        """Capture one phrase."""
        loop = asyncio.get_event_loop()
        with sr.Microphone() as source:
            logger.debug("Listening...")
            try:
                audio = await loop.run_in_executor(
                    None, 
                    lambda: self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
                )
                return audio
            except sr.WaitTimeoutError:
                return None

    async def _process_audio(self, audio: sr.AudioData) -> str:
        """Process raw audio to text."""
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
        """
        Handle user input with DialogueManager.
        REFACTORED: Now uses DialogueManager for all conversational logic.
        """
        if not text:
            return
            
        logger.info(f"User said: {text}")
        
        # Hardcoded system control commands
        if "stop voice" in text.lower() or "shutdown system" in text.lower():
            await self.speak("Shutting down voice loop.")
            self.stop()
            return
        
        # Process through DialogueManager
        response_data = await self.dialogue_manager.process_user_input(text)
        
        # Handle based on response type
        if response_data['response_type'] == ResponseType.EXECUTE:
            # Execute tools first
            for tool_call in response_data['tool_calls']:
                await self._execute_tool(tool_call)
            
            # Then speak response
            if response_data['text']:
                await self.speak(response_data['text'])
                await internal_bus.publish("assistant_message", {"text": response_data['text']})
        
        elif response_data['response_type'] == ResponseType.CONFIRM:
            # Ask for confirmation
            await self.speak(response_data['text'])
            await internal_bus.publish("assistant_message", {"text": response_data['text']})
        
        elif response_data['response_type'] == ResponseType.CLARIFY:
            # Request clarification
            await self.speak(response_data['text'])
            await internal_bus.publish("assistant_message", {"text": response_data['text']})
        
        else:  # ACKNOWLEDGE, UPDATE, ERROR
            # Just speak
            await self.speak(response_data['text'])
            await internal_bus.publish("assistant_message", {"text": response_data['text']})
        
        await internal_bus.publish("status_update", {"status": "idle"})

    async def _execute_tool(self, tool_call):
        """Execute a single tool call"""
        skill = self.skills.get(tool_call.tool_name)
        
        if not skill:
            logger.warning(f"Unknown tool: {tool_call.tool_name}")
            return
        
        logger.info(f"Executing tool: {tool_call.tool_name}", args=tool_call.arguments)
        
        try:
            # Map tool arguments to skill parameters
            if tool_call.tool_name == 'OPEN':
                result = await skill.execute({"app_name": tool_call.arguments})
            elif tool_call.tool_name == 'CMD':
                result = await skill.execute({"command": tool_call.arguments})
            elif tool_call.tool_name == 'GIT':
                result = await skill.execute({"command": tool_call.arguments})
            elif tool_call.tool_name == 'CODE':
                result = await skill.execute({"command": tool_call.arguments})
            elif tool_call.tool_name == 'SEARCH':
                result = await skill.execute({"command": tool_call.arguments})
            
            # Speak result
            await self.speak(result)
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_call.tool_name}", error=str(e))
            await self.speak(f"Failed to execute {tool_call.tool_name}: {str(e)}")

    def stop(self):
        self.is_running = False