import asyncio
from layers.intelligence.ollama_llm import OllamaLLM
from utils.logging import configure_logging

configure_logging()

async def main():
    print("Initializing Ollama for Memory Test...")
    llm = OllamaLLM()
    
    print("\n--- Turn 1 ---")
    p1 = "My name is BlackWidow."
    print(f"User: {p1}")
    r1 = await llm.generate_response(p1)
    print(f"Jarvis: {r1}")
    
    print("\n--- Turn 2 ---")
    p2 = "What is my name?"
    print(f"User: {p2}")
    r2 = await llm.generate_response(p2)
    print(f"Jarvis: {r2}")
    
    if "BlackWidow" in r2 or "BlackWidow" in r2:
        print("\nSUCCESS: Memory verified!")
    else:
        print("\nFAILURE: Did not remember name.")

if __name__ == "__main__":
    asyncio.run(main())
