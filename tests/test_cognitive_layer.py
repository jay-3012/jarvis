import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_cognitive():
    print("Testing Cognitive Layer...")
    
    try:
        from layers.cognitive.meta_agent import meta_agent
        print("✅ MetaAgent imported")
    except ImportError as e:
        print(f"❌ Failed to import MetaAgent: {e}")
        return

    print("Running process_request...")
    try:
        # Mocking LLM response for test if needed, but for now let's see if it runs
        # We might hit API errors if LLM service isn't reachable, but that's fine.
        result = await meta_agent.process_request("Find my secret plans")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_cognitive())
