from datetime import datetime, timedelta
from sqlalchemy import delete
from config.database import db, Message

class MessageCleanup:
    def __init__(self, retention_days: int = 30):
        """
        Initialize message cleanup manager.
        
        Args:
            retention_days: Number of days to keep messages (default: 30)
        """
        self.retention_days = retention_days

    async def cleanup_old_messages(self) -> int:
        """
        Remove messages older than retention period.
        
        Returns:
            int: Number of messages removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        try:
            with db.Session() as session:
                # Delete messages older than cutoff date
                delete_query = delete(Message).where(Message.created_at < cutoff_date)
                result = session.execute(delete_query)
                session.commit()
                
                # Get number of rows deleted
                rows_deleted = result.rowcount
                print(f"Cleaned up {rows_deleted} messages older than {cutoff_date}")
                return rows_deleted
                
        except Exception as e:
            print(f"Error during message cleanup: {e}")
            return 0