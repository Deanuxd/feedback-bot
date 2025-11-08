from dataclasses import dataclass
from discord import Member
from config.database import db

@dataclass
class ThreadInfo:
    thread_id: int
    nickname: str
    created_by: str
    description: str = None

def save_thread(thread_id: int, nickname: str, created_by: Member, description: str = None) -> bool:
    """Store thread information with a nickname."""
    return db.save_thread(thread_id, nickname, str(created_by), description)

def get_thread_by_name(nickname: str) -> ThreadInfo:
    """Retrieve thread information by nickname."""
    thread = db.get_thread_by_name(nickname)
    if thread:
        return ThreadInfo(
            thread_id=thread.thread_id,
            nickname=thread.nickname,
            created_by=thread.created_by,
            description=thread.description
        )
    return None

def get_thread_by_id(thread_id: int) -> ThreadInfo:
    """Retrieve thread information by ID."""
    thread = db.get_thread_by_id(thread_id)
    if thread:
        return ThreadInfo(
            thread_id=thread.thread_id,
            nickname=thread.nickname,
            created_by=thread.created_by,
            description=thread.description
        )
    return None