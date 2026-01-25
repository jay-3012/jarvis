# layers/dialogue/manager.py (UPDATED)

import asyncio
import structlog
import re
from typing import Dict, Any, Optional, List
from enum import Enum

from layers.dialogue.context import ConversationContext
from layers.dialogue.clarification import (  # NEW
    ClarificationDetector, 
    AmbiguityDetection,
    DisambiguationState,
    AmbiguityType
)
from layers.intelligence.ollama_llm import OllamaLLM
from core.event_bus import internal_bus

logger = structlog.get_logger()

class ResponseType(Enum):
    """Types of responses the dialogue manager can produce"""
    EXECUTE = "execute"
    CONFIRM = "confirm"
    CLARIFY = "clarify"          # NEW: Enhanced clarification
    UPDATE = "update"
    ERROR = "error"
    ACKNOWLEDGE = "acknowledge"

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
    NOW WITH CLARIFICATION DETECTION!
    """
    
    def __init__(self, llm: Optional[OllamaLLM] = None):
        self.llm = llm or OllamaLLM()
        self.context = ConversationContext()
        self.clarification_detector = ClarificationDetector(llm=self.llm)  # NEW
        self.pending_confirmation: Optional[Dict[str, Any]] = None
        self.disambiguation_state: Optional[DisambiguationState] = None  # NEW
        
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
        NOW WITH CLARIFICATION DETECTION!
        """
        logger.info("Processing user input", text=text)
        
        # 1. Add to conversation history
        self.context.add_turn("user", text)
        
        # 2. Check if this is a response to pending confirmation
        if self.pending_confirmation:
            return await self._handle_confirmation_response(text)
        
        # 3. Check if this is a response to disambiguation (NEW)
        if self.disambiguation_state:
            return await self._handle_disambiguation_response(text)
        
        # 4. DETECT AMBIGUITY FIRST (NEW)
        conversation_context = self.context.get_history_text()
        ambiguity = await self.clarification_detector.detect_ambiguity(
            text, 
            conversation_context
        )
        
        if ambiguity.is_ambiguous:
            logger.info("Ambiguity detected", type=ambiguity.ambiguity_type)
            return await self._create_clarification_request(text, ambiguity)
        
        # 5. Send to LLM if not ambiguous
        llm_response = await self._get_llm_response(text)
        
        # 6. Add assistant response to history
        self.context.add_turn("agent", llm_response)
        
        # 7. Parse for tool calls
        tool_calls = self._parse_tool_calls(llm_response)
        
        # 8. Determine response strategy
        response_data = await self._determine_response_strategy(
            llm_response, 
            tool_calls
        )
        
        return response_data
    
    async def _create_clarification_request(
        self, 
        original_text: str,
        ambiguity: AmbiguityDetection
    ) -> Dict[str, Any]:
        """
        Create a clarification request when ambiguity is detected.
        """
        
        # Store disambiguation state
        self.disambiguation_state = DisambiguationState(original_text, ambiguity)
        
        # Enhance with options if available
        enhanced_ambiguity = await self.clarification_detector.generate_options_from_context(
            ambiguity
        )
        
        # Format clarifying question with suggestions
        clarifying_text = enhanced_ambiguity.clarifying_question
        
        if enhanced_ambiguity.suggestions:
            suggestions_text = ", ".join(enhanced_ambiguity.suggestions)
            clarifying_text += f" (Options: {suggestions_text})"
        
        logger.info("Requesting clarification", 
                   question=clarifying_text,
                   ambiguity_type=ambiguity.ambiguity_type)
        
        return {
            'response_type': ResponseType.CLARIFY,
            'text': clarifying_text,
            'tool_calls': [],
            'needs_confirmation': False,
            'ambiguity_type': ambiguity.ambiguity_type,
            'suggestions': enhanced_ambiguity.suggestions
        }
    
    async def _handle_disambiguation_response(self, text: str) -> Dict[str, Any]:
        """
        Handle user's response to a clarification question.
        """
        
        if not self.disambiguation_state:
            return await self.process_user_input(text)  # Shouldn't happen
        
        # Store the clarification
        ambiguity_type = self.disambiguation_state.ambiguity.ambiguity_type
        self.disambiguation_state.add_clarification(ambiguity_type.value, text)
        
        # Reconstruct the original request with clarification
        resolved_request = self._reconstruct_request_with_clarification(
            self.disambiguation_state.original_request,
            text,
            ambiguity_type
        )
        
        logger.info("Clarification received", 
                   original=self.disambiguation_state.original_request,
                   clarification=text,
                   resolved=resolved_request)
        
        # Clear disambiguation state
        self.disambiguation_state = None
        
        # Process the resolved request
        llm_response = await self._get_llm_response(resolved_request)
        self.context.add_turn("agent", llm_response)
        
        tool_calls = self._parse_tool_calls(llm_response)
        
        return await self._determine_response_strategy(llm_response, tool_calls)
    
    def _reconstruct_request_with_clarification(
        self,
        original: str,
        clarification: str,
        ambiguity_type: AmbiguityType
    ) -> str:
        """
        Combine original request with clarification intelligently.
        IMPROVED: Better handling of different ambiguity types.
        """
        
        if ambiguity_type == AmbiguityType.VAGUE_REFERENCE:
            # Replace vague term with specific one
            original_lower = original.lower()
            
            # Try to replace each vague term
            for vague in ClarificationDetector.VAGUE_TERMS:
                if vague in original_lower:
                    # Replace intelligently
                    if vague.startswith("the "):
                        # "the file" → "report.pdf"
                        return original_lower.replace(vague, clarification)
                    elif vague in ["it", "that", "this"]:
                        # "Open it" → "Open report.pdf"
                        return original_lower.replace(vague, clarification)
            
            # Fallback
            return f"{original} {clarification}"
        
        elif ambiguity_type == AmbiguityType.TIME_AMBIGUITY:
            # Add time specification
            return f"{original} from {clarification}"
        
        elif ambiguity_type == AmbiguityType.MISSING_PARAMETER:
            # Append the missing parameter
            return f"{original} {clarification}"
        
        elif ambiguity_type == AmbiguityType.UNCLEAR_INTENT:
            # For LLM-detected ambiguity, just combine naturally
            return f"{original} - specifically: {clarification}"
        
        else:
            # Generic concatenation
            return f"{original} {clarification}"

    async def _get_llm_response(self, user_text: str) -> str:
        """Get response from LLM with conversation context"""
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
        """Decide how to respond based on LLM output and tool calls"""
        
        # Check for destructive actions
        has_destructive = any(
            tc.tool_name in self.destructive_actions 
            for tc in tool_calls
        )
        
        if has_destructive and not self.pending_confirmation:
            return await self._create_confirmation_request(llm_response, tool_calls)
        
        elif tool_calls:
            clean_response = self._remove_tool_syntax(llm_response)
            return {
                'response_type': ResponseType.EXECUTE,
                'text': clean_response,
                'tool_calls': tool_calls,
                'needs_confirmation': False
            }
        
        else:
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
        
        self.pending_confirmation = {
            'original_response': llm_response,
            'tool_calls': tool_calls
        }
        
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
        
        if any(word in text_lower for word in ['yes', 'proceed', 'go ahead', 'do it', 'confirm']):
            logger.info("User confirmed action")
            pending = self.pending_confirmation
            self.pending_confirmation = None
            
            clean_response = self._remove_tool_syntax(pending['original_response'])
            
            return {
                'response_type': ResponseType.EXECUTE,
                'text': f"Executing now. {clean_response}",
                'tool_calls': pending['tool_calls'],
                'needs_confirmation': False
            }
        
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
        
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text if clean_text else "Done."
    
    def clear_context(self):
        """Reset conversation context"""
        self.context.clear()
        self.pending_confirmation = None
        self.disambiguation_state = None
        logger.info("Conversation context cleared")
    
    def get_context_summary(self) -> str:
        """Get a summary of the current conversation state"""
        turns = len(self.context.history)
        has_pending = self.pending_confirmation is not None
        has_disambiguation = self.disambiguation_state is not None
        
        return (
            f"Conversation turns: {turns}, "
            f"Pending confirmation: {has_pending}, "
            f"Active disambiguation: {has_disambiguation}, "
            f"Active goal: {self.context.active_goal}"
        )