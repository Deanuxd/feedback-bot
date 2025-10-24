from config.database import db, Base, engine
from utils.migrate import migrate_log_to_db

def reset_database():
    """
    Drop all tables and recreate them.
    Optionally re-import data from feedback_log.txt.
    """
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    
    print("Creating new tables with updated schema...")
    Base.metadata.create_all(engine)
    
    try:
        print("Re-importing messages from feedback_log.txt...")
        count = migrate_log_to_db("feedback_log.txt", 1425907680479940688)
        print(f"Successfully imported {count} messages.")
    except FileNotFoundError:
        print("No feedback_log.txt found to import.")
    except Exception as e:
        print(f"Error during import: {e}")

if __name__ == "__main__":
    reset_database()