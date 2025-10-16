import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.db import Base, engine, db
from utils.migrate import migrate_log_to_db

def reset_database():
    """Drop all tables and recreate them."""
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    
    print("Creating new tables with updated schema...")
    Base.metadata.create_all(engine)
    
    print("Re-importing messages from feedback_log.txt...")
    count = migrate_log_to_db("feedback_log.txt", 1425907680479940688)
    print(f"Successfully imported {count} messages with role information.")

if __name__ == "__main__":
    reset_database()