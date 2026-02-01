import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_rag():
    print("Testing RAG Context...")
    
    try:
        from layers.cognitive.meta_agent import meta_agent
        print("✅ MetaAgent imported")
        
        # Test Query about the project (should trigger RAG)
        query = "Explain the architecture of the Cognitive Layer."
        print(f"\nUser: {query}")
        
        result = await meta_agent.process_request(query)
        print(f"\nResult Text:\n{result['text']}")
        
        # Check if plan/status indicates answer
        if result.get('status') == 'answered':
            print("\n✅ Successfully used RAG to answer without a plan.")
        else:
            print("\n⚠️  Generated a plan instead of direct answer (might be okay if plan is relevant).")
            
    except Exception as e:
        print(f"❌ Execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_rag())
