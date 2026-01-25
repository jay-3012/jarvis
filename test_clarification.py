# tests/test_clarification.py

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from layers.dialogue.manager import DialogueManager, ResponseType
from layers.dialogue.clarification import AmbiguityType

async def test_clarification_scenarios():
    """Test various clarification scenarios"""
    
    dm = DialogueManager()
    
    print("\n" + "="*70)
    print("CLARIFICATION DETECTION TESTS")
    print("="*70)
    
    # Test 1: Vague Reference
    print("\n[TEST 1] Vague Reference: 'Open the file'")
    print("-" * 70)
    response = await dm.process_user_input("Open the file")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    assert response['response_type'] == ResponseType.CLARIFY
    
    # User clarifies
    print("\nUser clarifies: 'report.pdf'")
    response = await dm.process_user_input("report.pdf")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    print(f"Tool Calls: {response['tool_calls']}")
    
    # Clear context for next test
    dm.clear_context()
    
    # Test 2: Time Ambiguity
    print("\n[TEST 2] Time Ambiguity: 'Delete old files'")
    print("-" * 70)
    response = await dm.process_user_input("Delete old files")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    assert response['response_type'] == ResponseType.CLARIFY
    
    # User clarifies
    print("\nUser clarifies: 'last month'")
    response = await dm.process_user_input("last month")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    
    dm.clear_context()
    
    # Test 3: Incomplete Command
    print("\n[TEST 3] Incomplete Command: 'Open'")
    print("-" * 70)
    response = await dm.process_user_input("Open")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    assert response['response_type'] == ResponseType.CLARIFY
    
    # User clarifies
    print("\nUser clarifies: 'notepad'")
    response = await dm.process_user_input("notepad")
    print(f"Response Type: {response['response_type']}")
    print(f"Tool Calls: {response['tool_calls']}")
    
    dm.clear_context()
    
    # Test 4: Clear Request (No Clarification Needed)
    print("\n[TEST 4] Clear Request: 'Open notepad'")
    print("-" * 70)
    response = await dm.process_user_input("Open notepad")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    print(f"Tool Calls: {response['tool_calls']}")
    # Should NOT trigger clarification
    assert response['response_type'] != ResponseType.CLARIFY
    
    dm.clear_context()
    
    # Test 5: Multiple Vague Terms
    print("\n[TEST 5] Multiple Vague: 'Send the email to the client'")
    print("-" * 70)
    response = await dm.process_user_input("Send the email to the client")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    # Should detect "the email" or "the client" as vague
    
    dm.clear_context()
    
    # Test 6: Context Reference
    print("\n[TEST 6] Context Reference: Multi-turn")
    print("-" * 70)
    await dm.process_user_input("I have three documents")
    response = await dm.process_user_input("Open it")
    print(f"Response Type: {response['response_type']}")
    print(f"Jarvis Says: {response['text']}")
    # Should ask which document
    assert response['response_type'] == ResponseType.CLARIFY
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)

async def test_llm_based_clarification():
    """Test LLM-based ambiguity detection"""
    
    print("\n" + "="*70)
    print("LLM-BASED CLARIFICATION TESTS")
    print("="*70)
    
    dm = DialogueManager()
    
    # Test complex ambiguity that rules can't catch
    print("\n[TEST] Complex: 'Email John about the meeting'")
    print("-" * 70)
    response = await dm.process_user_input("Email John about the meeting")
    print(f"Response Type: {response['response_type']}")
    dm.clear_context()

    print("\n[TEST] Complex: 'Prepare for the presentation'")
    print("-" * 70)
    response = await dm.process_user_input("Prepare for the presentation")
    print(f"Response Type: {response['response_type']}")
    dm.clear_context()

if __name__ == "__main__":
    print("\n🤖 Starting Clarification Detection Tests...\n")
    asyncio.run(test_clarification_scenarios())
    asyncio.run(test_llm_based_clarification())
