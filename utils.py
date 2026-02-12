from datetime import datetime, timedelta

def get_user_offset(username: str, user_dict: dict) -> float:
    """Get timezone offset (hours) for a username from provided dict."""
    if not username:
        return 0.0
    try:
        return float(user_dict.get(username.lower(), 0.0))
    except (TypeError, ValueError):
        return 0.0

def convert_utc_to_local(dt_utc: datetime, user_offset: float) -> datetime:
    """Convert UTC datetime to local time using hour offset."""
    return dt_utc + timedelta(hours=user_offset)

def format_time(seconds: int) -> str:
    """Format seconds as human-friendly minutes/seconds string."""
    m, s = divmod(seconds, 60)
    if m > 0:
        return f"{m}:{s:02d} min"
    return f"{s} sec"


def format_time_compact(seconds: int) -> str:
    """Format seconds as M:SS or Ss without unit labels."""
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}" if m > 0 else f"{s}s"


def escape_markdown(text: str) -> str:
    """Escape basic Markdown special characters in usernames/text."""
    return text.replace("_", "\\_").replace("*", "\\*")


def to_seconds(val: str | int) -> int:
    """
    Converts time strings to seconds.
    Supports: '1:10 min', '2:00', '50 sec', '10', '5 min'
    """
    s = str(val).lower()
    
    if ":" in s:
        # Удаляем любые буквы, оставляем только цифры и двоеточие
        clean_val = s.replace("min", "").replace("sec", "").strip()
        minutes, seconds = map(int, clean_val.split(":"))
        return minutes * 60 + seconds
    
    if "min" in s:
        clean_val = s.replace("min", "").strip()
        return int(clean_val) * 60
        
    clean_val = s.replace("sec", "").strip()
    return int(clean_val)


def validate_user(message) -> bool: # Using message from aiogram.types
    return bool(message.from_user and message.from_user.username)