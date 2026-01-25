# layers/dialogue/manager.py

import asyncio
import structlog
import re
from typing import Dict, Any, Optional, List
from enum import Enum

from layers.dialogue.context import ConversationContext
from layers.intelligence.ollama_llm import OllamaLLM
from core.event_bus import internal_bus

logger = structlog.get_logger()

class ResponseType(Enum):
    """Types of responses the dialogue manager can produce"""
    EXECUTE = "execute"           # Execute action immediately
    CONFIRM = "confirm"           # Ask for confirmation
    CLARIFY = "clarify"          # Request more information
    UPDATE = "update"            # Provide status update
    ERROR = "error"              # Report problem
    ACKNOWLEDGE = "acknowledge"   # Simple acknowledgment

class ToolCall:
    """Represents a parsed tool invocation"""
    def __init__(self, tool_name: str, arguments: str):
        self.tool_name = tool_name
        self.arguments = arguments
        
    def __repr__(self):
        return f"ToolCall({self.tool_name}: {self.arguments})"

class DialogueManager:
    """
    Manages conversational flow and decision-making.
    Responsibilities:
    - Maintain conversation context
    - Determine response strategy (execute/confirm/clarify)
    - Parse LLM responses for tool calls
    - Handle multi-turn dialogues
    - Manage pending confirmations
    """
    
    def __init__(self, llm: Optional[OllamaLLM] = None):
        self.llm = llm or OllamaLLM()
        self.context = ConversationContext()
        self.pending_confirmation: Optional[Dict[str, Any]] = None
        
        # Tool patterns for parsing
        self.tool_patterns = {
            'OPEN': r'\[\[OPEN:\s*(.*?)\]\]',
            'CMD': r'\[\[CMD:\s*(.*?)\]\]',
            'GIT': r'\[\[GIT:\s*(.*?)\]\]',
            'CODE': r'\[\[CODE:\s*(.*?)\]\]',
            'SEARCH': r'\[\[SEARCH:\s*(.*?)\]\]',
        }
        
        # Destructive actions requiring confirmation
        self.destructive_actions = ['CMD', 'GIT']
        
    async def process_user_input(self, text: str) -> Dict[str, Any]:
        """
        Main entry point for processing user input.
        
        Returns:
            {
                'response_type': ResponseType,
                'text': str,  # Text to speak to user
                'tool_calls': List[ToolCall],  # Tools to execute
                'needs_confirmation': bool
            }
        """
        logger.info("Processing user input", text=text)
        
        # 1. Add to conversation history
        self.context.add_turn("user", text)
        
        # 2. Check if this is a response to pending confirmation
        if self.pending_confirmation:
            return await self._handle_confirmation_response(text)
        
        # 3. Send to LLM with context
        llm_response = await self._get_llm_response(text)
        
        # 4. Add assistant response to history
        self.context.add_turn("agent", llm_response)
        
        # 5. Parse for tool calls
        tool_calls = self._parse_tool_calls(llm_response)
        
        # 6. Determine response strategy
        response_data = await self._determine_response_strategy(
            llm_response, 
            tool_calls
        )
        
        return response_data
    
    async def _get_llm_response(self, user_text: str) -> str:
        """Get response from LLM with conversation context"""
        # Build prompt with recent context
        context_text = self.context.get_history_text()
        
        # For now, just send the user text
        # The LLM already has history from OllamaLLM's internal history
        response = await self.llm.generate_response(user_text)
        
        return response
    
    def _parse_tool_calls(self, llm_response: str) -> List[ToolCall]:
        """Extract tool calls from LLM response using regex patterns"""
        tool_calls = []
        
        for tool_name, pattern in self.tool_patterns.items():
            matches = re.finditer(pattern, llm_response, re.IGNORECASE)
            for match in matches:
                arguments = match.group(1).strip()
                tool_calls.append(ToolCall(tool_name, arguments))
                logger.debug(f"Parsed tool call: {tool_name}", args=arguments)
        
        return tool_calls
    
    async def _determine_response_strategy(
        self, 
        llm_response: str, 
        tool_calls: List[ToolCall]
    ) -> Dict[str, Any]:
        """
        Decide how to respond based on the LLM output and tool calls.
        
        Strategy:
        1. If destructive tools -> CONFIRM
        2. If tools present -> EXECUTE
        3. If no tools -> ACKNOWLEDGE
        """
        
        # Check for destructive actions
        has_destructive = any(
            tc.tool_name in self.destructive_actions 
            for tc in tool_calls
        )
        
        if has_destructive and not self.pending_confirmation:
            # Need confirmation before executing
            return await self._create_confirmation_request(llm_response, tool_calls)
        
        elif tool_calls:
            # Execute tools
            clean_response = self._remove_tool_syntax(llm_response)
            return {
                'response_type': ResponseType.EXECUTE,
                'text': clean_response,
                'tool_calls': tool_calls,
                'needs_confirmation': False
            }
        
        else:
            # Just conversation, no tools
            return {
                'response_type': ResponseType.ACKNOWLEDGE,
                'text': llm_response,
                'tool_calls': [],
                'needs_confirmation': False
            }
    
    async def _create_confirmation_request(
        self, 
        llm_response: str, 
        tool_calls: List[ToolCall]
    ) -> Dict[str, Any]:
        """Create a confirmation request for destructive actions"""
        
        # Store pending action
        self.pending_confirmation = {
            'original_response': llm_response,
            'tool_calls': tool_calls
        }
        
        # Generate confirmation message
        tool_descriptions = ", ".join([
            f"{tc.tool_name}: {tc.arguments}" 
            for tc in tool_calls
        ])
        
        confirmation_text = (
            f"I'm about to execute: {tool_descriptions}. "
            f"Should I proceed?"
        )
        
        return {
            'response_type': ResponseType.CONFIRM,
            'text': confirmation_text,
            'tool_calls': [],
            'needs_confirmation': True
        }
    
    async def _handle_confirmation_response(self, text: str) -> Dict[str, Any]:
        """Handle user's response to a confirmation request"""
        
        text_lower = text.lower().strip()
        
        # Positive confirmations
        if any(word in text_lower for word in ['yes', 'proceed', 'go ahead', 'do it', 'confirm']):
            logger.info("User confirmed action")
            
            # Retrieve pending action
            pending = self.pending_confirmation
            self.pending_confirmation = None
            
            clean_response = self._remove_tool_syntax(pending['original_response'])
            
            return {
                'response_type': ResponseType.EXECUTE,
                'text': f"Executing now. {clean_response}",
                'tool_calls': pending['tool_calls'],
                'needs_confirmation': False
            }
        
        # Negative confirmations
        elif any(word in text_lower for word in ['no', 'cancel', 'stop', 'abort', 'don\'t']):
            logger.info("User cancelled action")
            self.pending_confirmation = None
            
            return {
                'response_type': ResponseType.ACKNOWLEDGE,
                'text': "Okay, I've cancelled that action.",
                'tool_calls': [],
                'needs_confirmation': False
            }
        
        else:
            # Unclear response - ask again
            return {
                'response_type': ResponseType.CLARIFY,
                'text': "I didn't understand. Should I proceed with the action? Please say yes or no.",
                'tool_calls': [],
                'needs_confirmation': True
            }
    
    def _remove_tool_syntax(self, text: str) -> str:
        """Remove [[TOOL: ...]] syntax from text for cleaner speech output"""
        clean_text = text
        for pattern in self.tool_patterns.values():
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text if clean_text else "Done."
    
    def clear_context(self):
        """Reset conversation context (for new session or testing)"""
        self.context.clear()
        self.pending_confirmation = None
        logger.info("Conversation context cleared")
    
    def get_context_summary(self) -> str:
        """Get a summary of the current conversation state"""
        turns = len(self.context.history)
        has_pending = self.pending_confirmation is not None
        
        return (
            f"Conversation turns: {turns}, "
            f"Pending confirmation: {has_pending}, "
            f"Active goal: {self.context.active_goal}"
        )