import os
# Fix for OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized.
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import asyncio
import sys
from utils.logging import configure_logging
from core.config import global_settings
from core.event_bus import internal_bus
import structlog

configure_logging()
logger = structlog.get_logger()

async def main():
    """
    Main entry point for Jarvis.
    """
    logger.info("Starting Jarvis...", version="0.1.0", env="development" if global_settings.DEBUG else "production")
    
    try:
        # Initialize Layers
        logger.info("Initializing layers...")
        
        # Phase 1: Voice Layer
        logger.info("Importing VoiceManager...")
        from layers.conversational.voice_manager import VoiceManager
        logger.info("Instantiating VoiceManager...")
        voice_manager = VoiceManager()
        logger.info("Initializing VoiceManager instance...")
        await voice_manager.initialize()
        
        await voice_manager.speak("Jarvis is online and listening.")
        
        # Start listening in background
        listen_task = asyncio.create_task(voice_manager.listen_loop())
        
        logger.info("Jarvis System Initialized. Waiting for events...")
        
        # Keep process alive and monitor loop
        await listen_task
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
    except Exception as e:
        logger.fatal("Critical system failure", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
