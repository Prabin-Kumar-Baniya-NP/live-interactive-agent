from typing import Optional

from app.schemas.base import BaseSchema


class HealthResponse(BaseSchema):
    status: str


class ReadinessResponse(HealthResponse):
    database: Optional[str] = "unknown"
    redis: Optional[str] = "unknown"
