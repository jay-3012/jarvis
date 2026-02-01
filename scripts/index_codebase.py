import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from layers.cognitive.memory import SemanticMemory
from layers.cognitive.context_loader import ContextLoader

def index_project():
    print("🚀 Starting Codebase Indexing...")
    
    # Initialize implementation
    # Note: ChromaDB persistence path should remain consistent
    memory = SemanticMemory(persistence_path="./chroma_db", collection_name="jarvis_context")
    loader = ContextLoader(memory)
    
    # Path to jarvis root
    # Assuming this script is in /scripts/
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    print(f"📂 Indexing directory: {root_path}")
    
    # Warning: This might duplicate data if run multiple times without clearing
    # For now, let's clear memory first to ensure fresh index
    print("🧹 Clearing old memory...")
    memory.clear_memory()
    
    print("reading files...")
    loader.load_directory(root_path)
    
    print("✅ Indexing Complete!")

if __name__ == "__main__":
    index_project()
