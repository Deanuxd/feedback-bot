from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

# Create the SQLAlchemy base class
Base = declarative_base()

class Thread(Base):
    """Thread model for storing Discord thread information."""
    __tablename__ = 'threads'

    thread_id = Column(Integer, primary_key=True)
    nickname = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)  # New field for thread description/context
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")

class Message(Base):
    """Message model for storing Discord messages."""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey('threads.thread_id'), nullable=False)
    author = Column(String, nullable=False)
    role = Column(String)  # Store user role (e.g., "Mod", "Dev", etc.)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    reply_to = Column(String)
    edited = Column(Boolean, default=False)

    # Relationship to thread
    thread = relationship("Thread", back_populates="messages")

    # Indexes for faster querying
    __table_args__ = (
        Index('idx_thread_id', 'thread_id'),
        Index('idx_created_at', 'created_at'),
    )