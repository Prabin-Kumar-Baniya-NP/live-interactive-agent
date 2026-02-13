from datetime import datetime
from typing import Optional
from uuid import UUID

from app.schemas.base import BaseSchema


class SessionStartRequest(BaseSchema):
    session_template_id: UUID
    user_id: Optional[str] = None


class SessionStartResponse(BaseSchema):
    session_id: UUID
    room_name: str
    access_token: str
    livekit_url: str
    token_expiry: datetime


class SessionStatusResponse(BaseSchema):
    id: UUID
    room_name: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
