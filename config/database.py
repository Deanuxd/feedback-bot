import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime

from models.database import Base, Thread, Message

class DatabaseConfig:
    """Database configuration and operations."""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database with optional custom connection URL.
        
        Args:
            db_url: Database URL. If not provided, uses DATABASE_URL from environment
                   or falls back to SQLite.
        """
        # Get database URL from environment or use default SQLite
        self.db_url = db_url or os.getenv(
            "DATABASE_URL", 
            "sqlite:///instance/feedback.db"
        )
        
        # Create engine and session factory
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Ensure instance directory exists for SQLite
        if self.db_url.startswith("sqlite"):
            os.makedirs("instance", exist_ok=True)
        
        # Create all tables
        Base.metadata.create_all(self.engine)

    def save_thread(self, thread_id: int, nickname: str, created_by: str) -> bool:
        """Save a thread to the database."""
        try:
            with self.Session() as session:
                thread = Thread(
                    thread_id=thread_id,
                    nickname=nickname,
                    created_by=created_by
                )
                session.add(thread)
                session.commit()
                return True
        except IntegrityError:
            return False

    def get_thread_by_name(self, nickname: str) -> Optional[Thread]:
        """Get thread info by nickname."""
        with self.Session() as session:
            return session.query(Thread).filter(Thread.nickname == nickname).first()

    def get_thread_by_id(self, thread_id: int) -> Optional[Thread]:
        """Get thread info by ID."""
        with self.Session() as session:
            return session.query(Thread).filter(Thread.thread_id == thread_id).first()

    def save_message(self, thread_id: int, author: str, content: str,
                    created_at: datetime, role: Optional[str] = None,
                    reply_to: Optional[str] = None, edited: bool = False) -> bool:
        """Save a message to the database."""
        try:
            with self.Session() as session:
                message = Message(
                    thread_id=thread_id,
                    author=author,
                    role=role,
                    content=content,
                    created_at=created_at,
                    reply_to=reply_to,
                    edited=edited
                )
                session.add(message)
                session.commit()
                return True
        except Exception:
            return False

    def get_messages(self, thread_id: int,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> List[Message]:
        """
        Get messages for a thread with optional date filtering.
        Returns a list of Message objects.
        """
        with self.Session() as session:
            query = session.query(Message).filter(Message.thread_id == thread_id)

            if start_date:
                query = query.filter(Message.created_at >= start_date)
            if end_date:
                query = query.filter(Message.created_at <= end_date)

            return query.order_by(Message.created_at.asc()).all()

# Create a global database instance
db = DatabaseConfig()