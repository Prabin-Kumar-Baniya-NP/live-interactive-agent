from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.models.enums import ModalityProfile, PanelType
from app.schemas.base import BaseSchema, TimestampSchema


class SessionTemplateBase(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    agent_ids: List[UUID]
    initial_agent_id: Optional[UUID] = None
    modality_profile: ModalityProfile = ModalityProfile.AUDIO_ONLY
    enabled_panels: List[str] = Field(default_factory=list)
    max_duration_seconds: Optional[int] = Field(None, gt=0)
    idle_timeout_seconds: int = Field(300, gt=0)

    @field_validator("enabled_panels")
    @classmethod
    def validate_enabled_panels(cls, v: List[str]) -> List[str]:
        # Validate that strings are valid PanelType values
        valid_panels = {p.value for p in PanelType}
        for panel in v:
            if panel not in valid_panels:
                raise ValueError(f"Invalid panel type: {panel}")
        return v

    @field_validator("agent_ids")
    @classmethod
    def validate_agent_ids(cls, v: List[UUID]) -> List[UUID]:
        if not v:
            raise ValueError("agent_ids must contain at least one agent ID")
        return v

    @model_validator(mode="after")
    def validate_initial_agent(self) -> "SessionTemplateBase":
        if self.initial_agent_id and self.initial_agent_id not in self.agent_ids:
            raise ValueError("initial_agent_id must be one of the agent_ids")
        return self


class SessionTemplateCreate(SessionTemplateBase):
    pass


class SessionTemplateUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    agent_ids: Optional[List[UUID]] = None
    initial_agent_id: Optional[UUID] = None
    modality_profile: Optional[ModalityProfile] = None
    enabled_panels: Optional[List[str]] = None
    max_duration_seconds: Optional[int] = Field(None, gt=0)
    idle_timeout_seconds: Optional[int] = Field(None, gt=0)

    @field_validator("enabled_panels")
    @classmethod
    def validate_enabled_panels(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        valid_panels = {p.value for p in PanelType}
        for panel in v:
            if panel not in valid_panels:
                raise ValueError(f"Invalid panel type: {panel}")
        return v

    @field_validator("agent_ids")
    @classmethod
    def validate_agent_ids(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if v is not None and not v:
            raise ValueError("agent_ids must contain at least one agent ID")
        return v

    @model_validator(mode="after")
    def validate_initial_agent(self) -> "SessionTemplateUpdate":
        # Note: In update, if only initial_agent_id is provided,
        # we can't fully validate against agent_ids unless we fetch from DB.
        # But this validation usually runs on the input data model.
        # If both are provided, we can validate.
        # If agent_ids is not provided,
        # we can't validate initial_agent_id here without DB context.
        # The service layer should handle cross-field validation with existing data.
        # However, if both are present in the update payload, let's validate.
        if self.initial_agent_id is not None and self.agent_ids is not None:
            if self.initial_agent_id not in self.agent_ids:
                raise ValueError(
                    "initial_agent_id must be in the provided agent_ids list"
                )
        return self


class SessionTemplateRead(SessionTemplateBase, TimestampSchema):
    id: UUID
    organization_id: UUID
    is_active: bool
