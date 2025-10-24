from datetime import datetime, timedelta
from typing import Tuple, Optional

def parse_timeframe(timeframe: Optional[str] = None) -> Tuple[datetime, datetime]:
    """
    Parse a timeframe string into start and end dates.
    
    Formats:
    - None or "24h": last 24 hours (default)
    - "3d": last 3 days
    - "1w": last week
    - "30d": last 30 days
    
    Returns:
    Tuple of (start_date, end_date) in UTC
    """
    end_date = datetime.utcnow()
    
    if not timeframe:
        timeframe = "24h"  # Default to last 24 hours
    
    # Parse the timeframe
    try:
        amount = int(timeframe[:-1])
        unit = timeframe[-1].lower()
        
        if unit == 'h':
            delta = timedelta(hours=amount)
        elif unit == 'd':
            delta = timedelta(days=amount)
        elif unit == 'w':
            delta = timedelta(weeks=amount)
        else:
            raise ValueError("Invalid time unit")
            
        # Ensure we don't exceed 30 days
        if delta > timedelta(days=30):
            delta = timedelta(days=30)
            
        start_date = end_date - delta
        return start_date, end_date
        
    except (IndexError, ValueError):
        # Default to 24 hours if parsing fails
        start_date = end_date - timedelta(hours=24)
        return start_date, end_date

def format_timeframe(start_date: datetime, end_date: datetime) -> str:
    """Format a timeframe range into a human-readable string."""
    delta = end_date - start_date
    
    if delta.days == 0:
        hours = delta.seconds // 3600
        return f"last {hours} hours"
    elif delta.days == 1:
        return "last 24 hours"
    elif delta.days == 7:
        return "last week"
    elif delta.days == 30:
        return "last 30 days"
    else:
        return f"last {delta.days} days"