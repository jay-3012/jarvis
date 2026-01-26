"""WebSocket protocol definitions and message types."""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Message Types
MessageType = Literal["ping", "pong", "command", "response", "notification", "error"]


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""
    type: MessageType
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    

class PingMessage(WebSocketMessage):
    """Heartbeat ping from client."""
    type: Literal["ping"] = "ping"
    device_id: str


class PongMessage(WebSocketMessage):
    """Heartbeat pong response from server."""
    type: Literal["pong"] = "pong"
    server_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CommandMessage(WebSocketMessage):
    """Command from server to device."""
    type: Literal["command"] = "command"
    command_id: str
    action: str
    params: dict = {}
    timeout: int = 30


class ResponseMessage(WebSocketMessage):
    """Response from device to server."""
    type: Literal["response"] = "response"
    command_id: str
    status: Literal["success", "error", "timeout"]
    data: Any = None
    error: Optional[str] = None


class NotificationMessage(WebSocketMessage):
    """Notification from server to device."""
    type: Literal["notification"] = "notification"
    title: str
    message: str
    priority: Literal["low", "normal", "high"] = "normal"


class ErrorMessage(WebSocketMessage):
    """Error message from server."""
    type: Literal["error"] = "error"
    error_code: str
    error_message: str
    details: Optional[dict] = None


# Protocol constants
HEARTBEAT_INTERVAL = 30  # seconds
CONNECTION_TIMEOUT = 90  # seconds
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
