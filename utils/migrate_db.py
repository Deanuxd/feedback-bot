import sqlite3
import os
from pathlib import Path

def migrate_database():
    """
    Migrate the database schema to add the description column to the threads table.
    """
    # Get the database path from environment or use default
    db_url = os.getenv("DATABASE_URL", "sqlite:///instance/feedback.db")
    
    # Extract the path from the SQLite URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url[10:]
    else:
        print(f"Unsupported database URL: {db_url}")
        return False
    
    # Ensure the database file exists
    if not Path(db_path).exists():
        print(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the description column already exists
        cursor.execute("PRAGMA table_info(threads)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "description" not in column_names:
            print("Adding 'description' column to threads table...")
            cursor.execute("ALTER TABLE threads ADD COLUMN description TEXT")
            conn.commit()
            print("Migration successful!")
        else:
            print("Column 'description' already exists in threads table.")
        
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database migration error: {e}")
        return False

if __name__ == "__main__":
    migrate_database()