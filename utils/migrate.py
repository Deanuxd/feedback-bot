import re
from datetime import datetime
from utils.db import db, Session
from sqlalchemy.exc import SQLAlchemyError

def parse_author_and_role(author_text: str) -> tuple[str, Optional[str]]:
    """Parse author text to extract role and username."""
    role_match = re.match(r'\[(.*?)\]\s*(.*)', author_text)
    if role_match:
        role, author = role_match.groups()
        return author.strip(), role.strip()
    return author_text.strip(), None

def parse_log_line(line: str):
    """Parse a line from feedback_log.txt into its components."""
    # Example line: [2025-10-16 14:25:30 EDT] [Mod] Username: Message content
    # Or: [2025-10-16 14:25:30 EDT] [Mod] Username (reply to Other User (2025-10-16 14:20:00)): Message content
    pattern = r'\[(.*?)\] (.*?)(?: \(reply to (.*?)\))?: (.*?)(?:  \[edited\])?$'
    match = re.match(pattern, line)
    if match:
        timestamp_str, author_text, reply_to, content = match.groups()
        try:
            # Parse the timestamp
            timestamp = datetime.strptime(timestamp_str.strip(), '%Y-%m-%d %H:%M:%S %Z')
            
            # Extract role if present
            author, role = parse_author_and_role(author_text)
            
            return {
                'timestamp': timestamp,
                'author': author,
                'role': role,
                'reply_to': reply_to.strip() if reply_to else None,
                'content': content.strip()
            }
        except ValueError:
            return None
    return None

def migrate_log_to_db(log_file: str, thread_id: int):
    """
    Migrate messages from a log file to the database.
    Uses SQLAlchemy transaction to ensure all messages are imported successfully.
    """
    imported = 0
    messages_to_import = []

    # First, parse all messages
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            parsed = parse_log_line(line)
            if parsed:
                messages_to_import.append({
                    'thread_id': thread_id,
                    'author': parsed['author'],
                    'role': parsed['role'],
                    'content': parsed['content'],
                    'created_at': parsed['timestamp'],
                    'reply_to': parsed['reply_to']
                })

    # Then import all messages in a single transaction
    if messages_to_import:
        try:
            with Session() as session:
                for message in messages_to_import:
                    success = db.save_message(**message)
                    if success:
                        imported += 1
                session.commit()
        except SQLAlchemyError as e:
            print(f"Error during migration: {e}")
            return 0
    
    return imported