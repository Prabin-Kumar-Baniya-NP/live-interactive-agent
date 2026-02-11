from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


class ErrorDetail(BaseSchema):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseSchema):
    error: ErrorDetail
