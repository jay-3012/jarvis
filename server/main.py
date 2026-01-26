"""Jarvis Central Server - FastAPI Application."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import os

from server.database import init_db, check_db_connection
from server.cache.redis_client import check_redis_connection
from server.services import check_ollama_connection
from utils.logging import configure_logging

# Configure logging
configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Jarvis Central Server...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    # Check connections
    if not check_db_connection():
        logger.error("Database connection failed")
        raise RuntimeError("Database connection failed")
    
    if not check_redis_connection():
        logger.warning("Redis connection failed - some features may be unavailable")
    
    logger.info("Jarvis Central Server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Jarvis Central Server...")


# Create FastAPI application
app = FastAPI(
    title="Jarvis Central Server",
    description="Multi-device AI ecosystem hub",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
from server.api import api_router
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Jarvis Central Server",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    checks = {
        "database": check_db_connection(),
        "redis": check_redis_connection(),
        "ollama": check_ollama_connection(),
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    
    return JSONResponse(
        status_code=200 if status == "healthy" else 503,
        content={
            "status": status,
            "checks": checks
        }
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    if not check_db_connection():
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "database unavailable"}
        )
    
    return {"status": "ready"}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, device_id: str = None):
    """
    WebSocket connection endpoint for devices.
    
    Query params:
        device_id: Unique identifier for the device
    """
    from server.websocket import manager, route_message
    
    if not device_id:
        await websocket.close(code=1008, reason="device_id required")
        return
    
    # Accept connection
    await manager.connect(websocket, device_id)
    
    try:
        while True:
            # Receive message from device
            data = await websocket.receive_json()
            logger.debug("WebSocket message received", device_id=device_id, message_type=data.get("type"))
            
            # Route message to appropriate handler
            await route_message(data, device_id)
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", device_id=device_id)
        manager.disconnect(device_id)
    except Exception as e:
        logger.error("WebSocket error", device_id=device_id, error=str(e))
        manager.disconnect(device_id)


@app.get("/devices")
async def list_devices():
    """List all connected devices."""
    from server.websocket import manager
    
    devices = []
    for device_id in manager.get_connected_devices():
        info = manager.get_device_info(device_id)
        devices.append({
            "device_id": device_id,
            **info
        })
    
    return {
        "total": len(devices),
        "devices": devices
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
