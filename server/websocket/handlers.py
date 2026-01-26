"""WebSocket message handlers."""

import structlog
from typing import Dict, Any
from server.websocket.protocol import (
    PingMessage, PongMessage, CommandMessage, ResponseMessage,
    NotificationMessage, ErrorMessage
)
from server.websocket.connection_manager import manager

logger = structlog.get_logger()


async def handle_ping(message: dict, device_id: str):
    """Handle ping message from device."""
    try:
        ping = PingMessage(**message)
        await manager.update_device_ping(device_id)
        
        # Send pong response
        pong = PongMessage()
        await manager.send_personal_message(pong.dict(), device_id)
        
        logger.debug("Ping handled", device_id=device_id)
    except Exception as e:
        logger.error("Failed to handle ping", device_id=device_id, error=str(e))


async def handle_response(message: dict, device_id: str):
    """Handle command response from device."""
    try:
        response = ResponseMessage(**message)
        logger.info(
            "Command response received",
            device_id=device_id,
            command_id=response.command_id,
            status=response.status
        )
        
        # TODO: Store response in database or cache
        # TODO: Notify waiting clients if any
        
    except Exception as e:
        logger.error("Failed to handle response", device_id=device_id, error=str(e))


async def handle_unknown(message: dict, device_id: str):
    """Handle unknown message types."""
    logger.warning("Unknown message type", device_id=device_id, message=message)
    
    error = ErrorMessage(
        error_code="UNKNOWN_MESSAGE_TYPE",
        error_message=f"Unknown message type: {message.get('type')}",
        details={"received_message": message}
    )
    await manager.send_personal_message(error.dict(), device_id)


# Message handler registry
MESSAGE_HANDLERS = {
    "ping": handle_ping,
    "response": handle_response,
}


async def route_message(message: dict, device_id: str):
    """Route incoming message to appropriate handler."""
    message_type = message.get("type")
    
    handler = MESSAGE_HANDLERS.get(message_type, handle_unknown)
    await handler(message, device_id)
