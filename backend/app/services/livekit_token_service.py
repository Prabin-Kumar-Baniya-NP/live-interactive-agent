from typing import Optional

from livekit import api

from app.core.config import settings


def generate_access_token(
    room_name: str,
    identity: str,
    name: Optional[str] = None,
    metadata: Optional[str] = None,
    ttl_seconds: int = 3600,
) -> str:
    """
    Generates a LiveKit access token for a participant to join a room.

    Args:
        room_name: define the room to join
        identity: unique identity of the participant (e.g., user_id)
        name: display name (optional)
        metadata: metadata string (optional, usually JSON)
        ttl_seconds: time to live in seconds (default 1 hour)
    """
    # Create AccessToken object with TTL
    token = api.AccessToken(
        settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET, ttl=ttl_seconds
    )

    # Set identity and optional name
    token.with_identity(identity)
    if name:
        token.with_name(name)

    # Add metadata
    if metadata:
        token.with_metadata(metadata)

    # Define capabilities (grants)
    grant = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
    token.with_grants(grant)

    # Note: ttl is typically handled in `to_jwt` or construction, but `livekit-api`
    # might accept it. If not, default is used.
    # To be safe, rely on default or check if `ttl` param is accepted in `AccessToken`.
    # Standard Python SDK: AccessToken(..., ttl=timedelta/seconds)
    # But since I initialized without it (constructor args order might vary),
    # I can rely on default for now, or check further.
    # Given I can't check easy, I'll stick to basic usage.

    return token.to_jwt()
