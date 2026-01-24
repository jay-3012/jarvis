import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.config import global_settings
    from core.event_bus import internal_bus
    from core.exceptions import FailureType, JarvisException
    from interfaces.agent import Agent, Executor
    from layers.dialogue.context import ConversationContext
    from utils.logging import configure_logging
    
    print("SUCCESS: All core modules imported successfully.")
except ImportError as e:
    print(f"FAILURE: Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Unexpected error: {e}")
    sys.exit(1)
