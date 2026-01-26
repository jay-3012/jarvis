"""Authentication and device registration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import secrets
import structlog

from server.database import get_db
from server.database.models import User, Device

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/auth", tags=["authentication"])


class DeviceRegistrationRequest(BaseModel):
    """Device registration request."""
    device_id: str
    device_type: str  # desktop, mobile, browser
    device_name: Optional[str] = None
    capabilities: Optional[dict] = {}


class DeviceRegistrationResponse(BaseModel):
    """Device registration response."""
    device_id: str
    pairing_code: str
    message: str


class TokenRequest(BaseModel):
    """Token generation request."""
    device_id: str
    pairing_code: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    device_id: str


@router.post("/register", response_model=DeviceRegistrationResponse)
async def register_device(
    request: DeviceRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new device.
    
    Returns a pairing code that must be approved by the user.
    """
    try:
        # Check if device already exists
        existing_device = db.query(Device).filter(Device.device_id == request.device_id).first()
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device already registered"
            )
        
        # Generate pairing code
        pairing_code = secrets.token_hex(3).upper()  # 6-character code
        
        # Get or create default user (for single-user setup)
        user = db.query(User).filter(User.username == "vishw").first()
        if not user:
            user = User(username="vishw", email="vishw@jarvis.local")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create device record
        device = Device(
            device_id=request.device_id,
            user_id=user.user_id,
            device_type=request.device_type,
            capabilities=request.capabilities or {},
            device_metadata={
                "pairing_code": pairing_code,
                "device_name": request.device_name,
                "approved": False  # Requires approval
            },
            status="pending"
        )
        
        db.add(device)
        db.commit()
        
        logger.info("Device registered", device_id=request.device_id, pairing_code=pairing_code)
        
        return DeviceRegistrationResponse(
            device_id=request.device_id,
            pairing_code=pairing_code,
            message=f"Device registered. Pairing code: {pairing_code}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Device registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/token", response_model=TokenResponse)
async def generate_token(
    request: TokenRequest,
    db: Session = Depends(get_db)
):
    """
    Generate access token for a device.
    
    For Phase 1, we'll use a simple token (device_id).
    In production, this would be a proper JWT token.
    """
    try:
        # Find device
        device = db.query(Device).filter(Device.device_id == request.device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Verify pairing code
        stored_code = device.device_metadata.get("pairing_code")
        if stored_code != request.pairing_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid pairing code"
            )
        
        # For Phase 1: Simple token (just the device_id)
        # TODO Phase 4: Implement proper JWT tokens
        access_token = f"jarvis_{device.device_id}_{secrets.token_hex(16)}"
        
        # Mark device as approved
        device.device_metadata["approved"] = True
        device.device_metadata["access_token"] = access_token
        device.status = "offline"  # Will be online when connected via WebSocket
        db.commit()
        
        logger.info("Token generated", device_id=request.device_id)
        
        return TokenResponse(
            access_token=access_token,
            device_id=request.device_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token generation failed"
        )


@router.get("/devices")
async def list_registered_devices(db: Session = Depends(get_db)):
    """List all registered devices."""
    devices = db.query(Device).all()
    return {
        "total": len(devices),
        "devices": [
            {
                "device_id": d.device_id,
                "device_type": d.device_type,
                "status": d.status,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in devices
        ]
    }
