from datetime import datetime
from typing import Optional, List
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import IntegrityError

# Create the SQLAlchemy base class
Base = declarative_base()

# Create database engine - can be changed to PostgreSQL by updating this line
engine = create_engine("sqlite:///feedback.db", echo=False)
Session = sessionmaker(bind=engine)

class Thread(Base):
    __tablename__ = 'threads'

    thread_id = Column(Integer, primary_key=True)
    nickname = Column(String, unique=True, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")

class Message(Base):
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

class Database:
    def __init__(self, db_url: str = None):
        """Initialize database with optional custom connection URL."""
        if db_url:
            global engine, Session
            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
        
        # Create all tables
        Base.metadata.create_all(engine)

    def save_thread(self, thread_id: int, nickname: str, created_by: str) -> bool:
        """Save a thread to the database."""
        try:
            with Session() as session:
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
        with Session() as session:
            return session.query(Thread).filter(Thread.nickname == nickname).first()

    def get_thread_by_id(self, thread_id: int) -> Optional[Thread]:
        """Get thread info by ID."""
        with Session() as session:
            return session.query(Thread).filter(Thread.thread_id == thread_id).first()

    def save_message(self, thread_id: int, author: str, content: str,
                    created_at: datetime, role: Optional[str] = None,
                    reply_to: Optional[str] = None, edited: bool = False) -> bool:
        """Save a message to the database."""
        try:
            with Session() as session:
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
        with Session() as session:
            query = session.query(Message).filter(Message.thread_id == thread_id)

            if start_date:
                query = query.filter(Message.created_at >= start_date)
            if end_date:
                query = query.filter(Message.created_at <= end_date)

            return query.order_by(Message.created_at.asc()).all()

# Create a global database instance
db = Database()

# Example of how to switch to PostgreSQL:
"""
To use PostgreSQL instead of SQLite, initialize the database with a PostgreSQL URL:

db = Database("postgresql://user:pass@localhost/dbname")

Or set it via environment variable:

db = Database(os.getenv("DATABASE_URL", "sqlite:///feedback.db"))
"""