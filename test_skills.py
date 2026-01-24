import asyncio
from layers.intelligence.ollama_llm import OllamaLLM
from layers.skills.app_launcher import AppLauncher
from utils.logging import configure_logging

configure_logging()

async def main():
    print("--- 1. Testing LLM Command Generation ---")
    llm = OllamaLLM()
    prompt = "Please open the calculator for me."
    print(f"User: {prompt}")
    
    response = await llm.generate_response(prompt)
    print(f"Jarvis: {response}")
    
    if "[[OPEN: calculator]]" in response.lower() or "[[open: calc]]" in response.lower() or "[[open: calculator]]" in response.lower():
        print("SUCCESS: LLM generated command.")
    else:
        print("WARNING: LLM did not generate exact command. Check output above.")

    print("\n--- 2. Testing App Launcher ---")
    launcher = AppLauncher()
    print("Attempting to launch Calculator...")
    result = await launcher.execute({"app_name": "calculator"})
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
