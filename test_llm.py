import asyncio
from layers.intelligence.ollama_llm import OllamaLLM
from utils.logging import configure_logging

configure_logging()

async def main():
    print("Initializing Ollama...")
    llm = OllamaLLM()
    
    print("Sending test prompt: 'Hello, who are you?'")
    try:
        response = await llm.generate_response("Hello, who are you? Keep it brief.")
        print(f"\n--- RESPONSE ---\n{response}\n----------------")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
