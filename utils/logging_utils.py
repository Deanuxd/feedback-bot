from datetime import datetime, timezone
from typing import Optional
from config.database import db

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("America/New_York")  # change if needed
except Exception:
    # Fallback: if zoneinfo not available, you can pip install pytz and use that instead:
    # import pytz
    # LOCAL_TZ = pytz.timezone("America/New_York")
    LOCAL_TZ = timezone.utc  # conservative fallback

def to_local_str(dt: datetime) -> str:
    """
    Convert a Discord message datetime (dt) to a local timezone string.
    Handles both tz-aware and naive datetimes safely.
    """
    if dt is None:
        return "unknown-time"

    # If tz-aware, convert to local
    if dt.tzinfo is not None:
        local_dt = dt.astimezone(LOCAL_TZ)
    else:
        # Assume naive timestamps are already in local time
        local_dt = dt

    tz_abbr = local_dt.tzname() or ""
    return local_dt.strftime(f"%Y-%m-%d %H:%M:%S {tz_abbr}")

def log_message(author: str, content: str, created_at: datetime, 
                thread_id: int, reply_to: Optional[str] = None, 
                edited: bool = False) -> None:
    """Store a message in the database with thread association."""
    success = db.save_message(
        thread_id=thread_id,
        author=author,
        content=content,
        created_at=created_at,
        reply_to=reply_to,
        edited=edited
    )
    
    # Print to console for debugging
    timestamp = to_local_str(created_at)
    if reply_to:
        base_line = f"[{timestamp}] {author} (reply to {reply_to}): {content}"
    else:
        base_line = f"[{timestamp}] {author}: {content}"

    if edited:
        base_line += " [edited]"

    print(f"Thread {thread_id}: {base_line}")