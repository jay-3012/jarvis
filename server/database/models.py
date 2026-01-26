"""SQLAlchemy database models for Jarvis Central Server."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, CheckConstraint, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class User(Base):
    """User model - represents a Jarvis user."""
    
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    preferences = Column(JSONB, default={})
    
    # Relationships
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}')>"


class Device(Base):
    """Device model - represents a connected device (desktop, mobile, browser)."""
    
    __tablename__ = "devices"
    
    device_id = Column(String(100), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    device_type = Column(String(20), nullable=False)
    capabilities = Column(JSONB, default={})
    last_seen = Column(DateTime)
    status = Column(String(20), default="offline")
    device_metadata = Column(JSONB, default={})  # Renamed from 'metadata'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="devices")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("device_type IN ('desktop', 'mobile', 'browser')", name="check_device_type"),
        CheckConstraint("status IN ('online', 'offline', 'away')", name="check_status"),
        Index("idx_devices_user_id", "user_id"),
        Index("idx_devices_status", "status"),
        Index("idx_devices_last_seen", "last_seen"),
    )
    
    def __repr__(self):
        return f"<Device(device_id='{self.device_id}', type='{self.device_type}', status='{self.status}')>"


class Conversation(Base):
    """Conversation model - represents a dialogue session."""
    
    __tablename__ = "conversations"
    
    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime)
    device_id = Column(String(100))
    conversation_metadata = Column(JSONB, default={})  # Renamed from 'metadata'
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_device_id", "device_id"),
        Index("idx_conversations_last_message", "last_message_at"),
    )
    
    def __repr__(self):
        return f"<Conversation(id='{self.conversation_id}', user_id='{self.user_id}')>"


class Message(Base):
    """Message model - represents a single message in a conversation."""
    
    __tablename__ = "messages"
    
    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False)
    speaker = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSONB, default={})  # Renamed from 'metadata'
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("speaker IN ('user', 'assistant', 'system')", name="check_speaker"),
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<Message(speaker='{self.speaker}', content='{self.content[:30]}...')>"


class AuditLog(Base):
    """Audit log model - tracks all system actions for security and debugging."""
    
    __tablename__ = "audit_logs"
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    device_id = Column(String(100))
    action = Column(String(100), nullable=False)
    details = Column(JSONB, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(INET)
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_device", "device_id"),
        Index("idx_audit_action", "action"),
    )
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', device_id='{self.device_id}')>"
