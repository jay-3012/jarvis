"""Command execution API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import structlog

from server.database import get_db
from server.websocket import manager, CommandMessage

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/commands", tags=["commands"])


class CommandExecutionRequest(BaseModel):
    """Command execution request."""
    device_id: str
    action: str
    params: Dict[str, Any] = {}
    timeout: int = 30


class CommandExecutionResponse(BaseModel):
    """Command execution response."""
    command_id: str
    status: str
    message: str


@router.post("/execute", response_model=CommandExecutionResponse)
async def execute_command(
    request: CommandExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a command on a specific device.
    
    The command is sent via WebSocket to the device.
    """
    try:
        # Check if device is connected
        if not manager.is_connected(request.device_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {request.device_id} is not connected"
            )
        
        # Generate command ID
        command_id = str(uuid.uuid4())
        
        # Create command message
        command = CommandMessage(
            command_id=command_id,
            action=request.action,
            params=request.params,
            timeout=request.timeout
        )
        
        # Send command to device via WebSocket
        await manager.send_personal_message(command.dict(), request.device_id)
        
        logger.info(
            "Command sent to device",
            command_id=command_id,
            device_id=request.device_id,
            action=request.action
        )
        
        return CommandExecutionResponse(
            command_id=command_id,
            status="sent",
            message=f"Command sent to device {request.device_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Command execution failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Command execution failed"
        )
