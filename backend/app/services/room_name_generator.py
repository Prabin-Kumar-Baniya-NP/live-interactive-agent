import secrets
from datetime import datetime, timezone


def generate_room_name() -> str:
    """
    Generates a unique, URL-safe room name.
    Format: session_{timestamp}_{random_suffix}
    Example: session_20260212_143022_a7b3c9
    Maximum length: 64 characters (LiveKit limitation)
    """
    # Use UTC timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Generate 3 bytes = 6 hex characters
    random_suffix = secrets.token_hex(3)

    room_name = f"session_{timestamp}_{random_suffix}"

    # Ensure strict 64 char limit, though this format is only ~24 chars
    return room_name[:64]
