"""WebSocket connection manager for device connections."""

from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import structlog
import json
import asyncio
from datetime import datetime

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for all devices."""
    
    def __init__(self):
        # Active connections: {device_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Device metadata: {device_id: {type, last_ping, etc}}
        self.device_metadata: Dict[str, dict] = {}
        
    async def connect(self, websocket: WebSocket, device_id: str, device_type: str = "unknown"):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[device_id] = websocket
        self.device_metadata[device_id] = {
            "device_type": device_type,
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat(),
            "status": "online"
        }
        logger.info("Device connected", device_id=device_id, device_type=device_type)
        
    def disconnect(self, device_id: str):
        """Remove a device connection."""
        if device_id in self.active_connections:
            del self.active_connections[device_id]
        if device_id in self.device_metadata:
            self.device_metadata[device_id]["status"] = "offline"
        logger.info("Device disconnected", device_id=device_id)
        
    async def send_personal_message(self, message: dict, device_id: str):
        """Send a message to a specific device."""
        if device_id in self.active_connections:
            try:
                websocket = self.active_connections[device_id]
                await websocket.send_json(message)
                logger.debug("Message sent to device", device_id=device_id, message_type=message.get("type"))
            except Exception as e:
                logger.error("Failed to send message", device_id=device_id, error=str(e))
                self.disconnect(device_id)
        else:
            logger.warning("Device not connected", device_id=device_id)
            
    async def broadcast(self, message: dict, exclude: Set[str] = None):
        """Broadcast a message to all connected devices (optionally excluding some)."""
        exclude = exclude or set()
        disconnected = []
        
        for device_id, websocket in self.active_connections.items():
            if device_id not in exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error("Broadcast failed", device_id=device_id, error=str(e))
                    disconnected.append(device_id)
        
        # Clean up disconnected devices
        for device_id in disconnected:
            self.disconnect(device_id)
            
    def get_connected_devices(self) -> list:
        """Get list of all connected device IDs."""
        return list(self.active_connections.keys())
    
    def is_connected(self, device_id: str) -> bool:
        """Check if a device is currently connected."""
        return device_id in self.active_connections
    
    def get_device_info(self, device_id: str) -> dict:
        """Get metadata for a specific device."""
        return self.device_metadata.get(device_id, {})
    
    async def update_device_ping(self, device_id: str):
        """Update last ping timestamp for a device."""
        if device_id in self.device_metadata:
            self.device_metadata[device_id]["last_ping"] = datetime.utcnow().isoformat()


# Global connection manager instance
manager = ConnectionManager()
