import asyncio
import os
import shutil
from layers.intelligence.ollama_llm import OllamaLLM
from layers.skills.system_commander import SystemCommander
from utils.logging import configure_logging

configure_logging()

async def main():
    print("--- 1. Testing LLM CMD Generation ---")
    llm = OllamaLLM()
    prompt = "Create a folder named 'TestFolder123'."
    print(f"User: {prompt}")
    
    response = await llm.generate_response(prompt)
    print(f"Jarvis: {response}")
    
    if "[[CMD:" in response and "mkdir" in response.lower():
        print("SUCCESS: LLM generated CMD command.")
    else:
        print("WARNING: Check LLM output.")

    print("\n--- 2. Testing System Commander Execution ---")
    commander = SystemCommander()
    cmd = "mkdir TestFolder123"
    print(f"Executing: {cmd}")
    
    result = await commander.execute({"command": cmd})
    print(f"Result: {result}")
    
    # Verify existence
    if os.path.exists("TestFolder123"):
        print("SUCCESS: Folder created.")
        # Cleanup
        os.rmdir("TestFolder123")
    else:
        print("FAILURE: Folder not found.")

if __name__ == "__main__":
    asyncio.run(main())
