import os
# Fix for OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized.
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import asyncio
import structlog
import flet as ft
from core.config import global_settings
from layers.conversational.voice_manager import VoiceManager
from utils.logging import configure_logging
from ui.main_window import JarvisUI

configure_logging()
logger = structlog.get_logger()

async def start_voice_loop():
    """Background task for voice manager."""
    logger.info("Starting Voice Loop in background...")
    try:
        vm = VoiceManager()
        await vm.initialize()
        await vm.listen_loop()
    except Exception as e:
        logger.error("Voice Loop Crashed", error=str(e))

async def main(page: ft.Page):
    """Flet Entry Point."""
    logger.info("Initializing UI...")
    
    # 1. Initialize UI
    ui = JarvisUI(page)
    
    # 2. Start Voice Loop in Background
    # page.run_task allows running an async task within Flet's loop
    page.run_task(start_voice_loop)

if __name__ == "__main__":
    logger.info("Starting JARVIS System (UI Mode)...")
    try:
        # ft.app runs the main event loop
        ft.app(target=main)
    except Exception as e:
        logger.error("Application Crash", error=str(e))
