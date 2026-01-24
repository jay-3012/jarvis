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
        # TODO: Initialize Layers
        # conversational_layer.init()
        # dialogue_layer.init()
        # cognitive_layer.init()
        # execution_layer.init()
        
        logger.info("Jarvis System Initialized. Waiting for events...")
        
        # Keep process alive
        while True:
            await asyncio.sleep(1)
            
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
