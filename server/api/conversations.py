"""Conversation management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import structlog

from server.database import get_db
from server.database.models import Conversation, Message, User

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


class MessageCreate(BaseModel):
    """Message creation request."""
    speaker: str  # user, assistant, system
    content: str


class MessageResponse(BaseModel):
    """Message response."""
    message_id: str
    speaker: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Conversation response."""
    conversation_id: str
    started_at: str
    last_message_at: Optional[str]
    device_id: Optional[str]
    message_count: int


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    device_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    try:
        # Get default user
        user = db.query(User).filter(User.username == "vishw").first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create conversation
        conversation = Conversation(
            user_id=user.user_id,
            device_id=device_id,
            started_at=datetime.utcnow()
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        logger.info("Conversation created", conversation_id=str(conversation.conversation_id))
        
        return ConversationResponse(
            conversation_id=str(conversation.conversation_id),
            started_at=conversation.started_at.isoformat(),
            last_message_at=None,
            device_id=device_id,
            message_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create conversation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a message to a conversation."""
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.conversation_id == uuid.UUID(conversation_id)
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Create message
        msg = Message(
            conversation_id=conversation.conversation_id,
            speaker=message.speaker,
            content=message.content,
            timestamp=datetime.utcnow()
        )
        
        db.add(msg)
        
        # Update conversation last_message_at
        conversation.last_message_at = msg.timestamp
        
        db.commit()
        db.refresh(msg)
        
        logger.info("Message added", message_id=str(msg.message_id), conversation_id=conversation_id)
        
        return MessageResponse(
            message_id=str(msg.message_id),
            speaker=msg.speaker,
            content=msg.content,
            timestamp=msg.timestamp.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add message", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message"
        )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get messages from a conversation."""
    try:
        messages = db.query(Message).filter(
            Message.conversation_id == uuid.UUID(conversation_id)
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        return [
            MessageResponse(
                message_id=str(msg.message_id),
                speaker=msg.speaker,
                content=msg.content,
                timestamp=msg.timestamp.isoformat()
            )
            for msg in reversed(messages)
        ]
        
    except Exception as e:
        logger.error("Failed to get messages", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List recent conversations."""
    try:
        conversations = db.query(Conversation).order_by(
            Conversation.started_at.desc()
        ).limit(limit).all()
        
        result = []
        for conv in conversations:
            message_count = db.query(Message).filter(
                Message.conversation_id == conv.conversation_id
            ).count()
            
            result.append(ConversationResponse(
                conversation_id=str(conv.conversation_id),
                started_at=conv.started_at.isoformat(),
                last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None,
                device_id=conv.device_id,
                message_count=message_count
            ))
        
        return result
        
    except Exception as e:
        logger.error("Failed to list conversations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )
