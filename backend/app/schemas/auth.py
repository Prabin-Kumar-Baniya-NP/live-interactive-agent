from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupBaseSchema(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class SignupSchema(SignupBaseSchema):
    password: str = Field(..., min_length=8)
    organization_name: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserSchema(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GenericMessageSchema(BaseModel):
    message: str
