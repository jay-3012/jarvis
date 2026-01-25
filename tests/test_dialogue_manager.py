# tests/test_dialogue_manager.py

import asyncio
from layers.dialogue.manager import DialogueManager, ResponseType

async def test_dialogue():
    dm = DialogueManager()
    
    # Test 1: Simple conversation
    print("\n=== Test 1: Simple Conversation ===")
    response = await dm.process_user_input("Hello Jarvis, what time is it?")
    print(f"Response Type: {response['response_type']}")
    print(f"Text: {response['text']}")
    print(f"Tool Calls: {response['tool_calls']}")
    
    # Test 2: Tool execution (safe)
    print("\n=== Test 2: Safe Tool Execution ===")
    response = await dm.process_user_input("Open notepad")
    print(f"Response Type: {response['response_type']}")
    print(f"Tool Calls: {response['tool_calls']}")
    
    # Test 3: Destructive action requiring confirmation
    print("\n=== Test 3: Destructive Action (CMD) ===")
    response = await dm.process_user_input("Delete all temporary files")
    print(f"Response Type: {response['response_type']}")
    print(f"Needs Confirmation: {response['needs_confirmation']}")
    print(f"Text: {response['text']}")
    
    # Test 4: User confirms
    print("\n=== Test 4: User Confirms ===")
    response = await dm.process_user_input("Yes, proceed")
    print(f"Response Type: {response['response_type']}")
    print(f"Tool Calls: {response['tool_calls']}")
    
    # Test 5: Context summary
    print("\n=== Test 5: Context Summary ===")
    print(dm.get_context_summary())

if __name__ == "__main__":
    asyncio.run(test_dialogue())