import re
from datetime import datetime
from config.database import db
from sqlalchemy.exc import SQLAlchemyError

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
            role_match = re.match(r'\[(.*?)\]\s*(.*)', author_text)
            if role_match:
                role, author = role_match.groups()
            else:
                role, author = None, author_text
            
            return {
                'timestamp': timestamp,
                'author': author.strip(),
                'role': role.strip() if role else None,
                'reply_to': reply_to.strip() if reply_to else None,
                'content': content.strip()
            }
        except ValueError:
            return None
    return None

def migrate_log_to_db(log_file: str, thread_id: int) -> int:
    """
    Migrate messages from a log file to the database.
    Uses SQLAlchemy transaction to ensure all messages are imported successfully.
    
    Args:
        log_file: Path to the log file
        thread_id: ID of the thread to associate messages with
        
    Returns:
        int: Number of messages imported
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
            with db.Session() as session:
                for message in messages_to_import:
                    success = db.save_message(**message)
                    if success:
                        imported += 1
                session.commit()
        except SQLAlchemyError as e:
            print(f"Error during migration: {e}")
            return 0
    
    return imported