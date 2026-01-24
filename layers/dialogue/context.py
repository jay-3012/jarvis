from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

class ConversationTurn(BaseModel):
    """Represents a single exchange in the conversation."""
    timestamp: float = Field(default_factory=time.time)
    speaker: str  # "user" or "agent"
    content: str
    intent: Optional[Dict[str, Any]] = None

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

    def add_turn(self, speaker: str, content: str, intent: Optional[Dict[str, Any]] = None) -> None:
        """Record a new turn."""
        turn = ConversationTurn(speaker=speaker, content=content, intent=intent)
        self.history.append(turn)

    def get_history_text(self) -> str:
        """Return formatted history for LLM context."""
        return "\n".join([f"{t.speaker}: {t.content}" for t in self.history])

    def clear(self) -> None:
        """Reset context (for testing or new session)."""
        self.history = []
        self.active_goal = None
        self.pending_confirmations = []
