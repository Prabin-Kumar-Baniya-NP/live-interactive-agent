import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AgentModality, PanelType  # noqa


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False, default="gpt-4.1-mini")
    voice: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    handoff_targets: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(Uuid), nullable=True, server_default="{}"
    )
    tools: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, server_default="{}"
    )
    modality: Mapped[AgentModality] = mapped_column(
        Enum(
            AgentModality,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=AgentModality.AUDIO_ONLY,
        server_default=AgentModality.AUDIO_ONLY.value,
        nullable=False,
    )
    panels: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, server_default="{}"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    current_version: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )

    # Relationships
    organization = relationship("Organization", back_populates="agents")
    versions = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="desc(AgentVersion.version)",
    )
