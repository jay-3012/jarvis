# layers/dialogue/context.py (UPDATED)

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

class ConversationTurn(BaseModel):
    """Represents a single exchange in the conversation."""
    timestamp: float = Field(default_factory=time.time)
    speaker: str  # "user" or "agent"
    content: str
    intent: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[str]] = None  # NEW: Track what tools were called

class ConversationContext:
    """
    Manages the state of the current conversation session.
    Single source of truth.
    """
    def __init__(self):
        self.history: List[ConversationTurn] = []
        self.active_goal: Optional[str] = None
        self.pending_confirmations: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}

    def add_turn(
        self, 
        speaker: str, 
        content: str, 
        intent: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[str]] = None
    ) -> None:
        """Record a new turn."""
        turn = ConversationTurn(
            speaker=speaker, 
            content=content, 
            intent=intent,
            tool_calls=tool_calls
        )
        self.history.append(turn)

    def get_history_text(self, window: int = 5) -> str:
        """Return formatted history for LLM context (last N turns)."""
        recent_history = self.history[-window:] if len(self.history) > window else self.history
        return "\n".join([f"{t.speaker}: {t.content}" for t in recent_history])
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message"""
        for turn in reversed(self.history):
            if turn.speaker == "user":
                return turn.content
        return None
    
    def get_last_agent_message(self) -> Optional[str]:
        """Get the most recent agent message"""
        for turn in reversed(self.history):
            if turn.speaker == "agent":
                return turn.content
        return None

    def clear(self) -> None:
        """Reset context (for testing or new session)."""
        self.history = []
        self.active_goal = None
        self.pending_confirmations = []