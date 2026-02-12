from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import AgentModality, PanelType
from app.schemas.base import BaseSchema, TimestampSchema


class AgentCreate(BaseSchema):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Display name of the agent"
    )
    instructions: str = Field(
        ..., min_length=1, description="System prompt for the agent"
    )
    model: str = Field("gpt-4.1-mini", description="LLM model identifier")
    voice: Optional[str] = Field(None, description="TTS voice identifier")
    handoff_targets: List[UUID] = Field(
        default_factory=list,
        description="List of agent UUIDs this agent can hand off to",
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tool identifiers assigned to this agent",
    )
    modality: AgentModality = Field(
        AgentModality.AUDIO_ONLY, description="Input modality required by the agent"
    )
    panels: List[PanelType] = Field(
        default_factory=list,
        description="List of workspace panels assigned to this agent",
    )

    @field_validator("panels")
    @classmethod
    def validate_unique_panels(cls, v: List[PanelType]) -> List[PanelType]:
        return list(set(v))


class AgentUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    instructions: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = None
    voice: Optional[str] = None
    handoff_targets: Optional[List[UUID]] = None
    tools: Optional[List[str]] = None
    modality: Optional[AgentModality] = None
    panels: Optional[List[PanelType]] = None
    is_active: Optional[bool] = None

    @field_validator("panels")
    @classmethod
    def validate_unique_panels(
        cls, v: Optional[List[PanelType]]
    ) -> Optional[List[PanelType]]:
        if v is None:
            return None
        return list(set(v))


class AgentRead(TimestampSchema):
    id: UUID
    organization_id: UUID
    name: str
    instructions: str
    model: str
    voice: Optional[str] = None
    handoff_targets: List[UUID]
    tools: List[str]
    modality: AgentModality
    panels: List[str]
    is_active: bool


class AgentVersionRead(TimestampSchema):
    id: UUID
    agent_id: UUID
    version: int
    snapshot: dict
    created_at: datetime


class AgentExport(BaseSchema):
    name: str
    instructions: str
    model: str
    voice: Optional[str] = None
    modality: AgentModality
    panels: List[PanelType]
    tools: List[str]


class AgentImportRequest(BaseSchema):
    agents: List[AgentExport]


class AgentImportResponse(BaseSchema):
    created: int
    skipped: int
    agents: List[AgentRead]
