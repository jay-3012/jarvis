"""API package initialization."""

from fastapi import APIRouter
from server.api import auth, commands, conversations

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(commands.router)
api_router.include_router(conversations.router)

__all__ = ["api_router"]
