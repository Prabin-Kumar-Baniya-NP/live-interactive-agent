import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.session import Session
from app.models.session_template import SessionTemplate
from app.schemas.session import SessionStartResponse, SessionStatusResponse
from app.services.livekit_token_service import generate_access_token
from app.services.room_name_generator import generate_room_name


class SessionService:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        session_template_id: UUID,
        organization_id: UUID,
        user_id: Optional[str] = None,
    ) -> SessionStartResponse:
        """
        Creates a new session from a template.
        """
        # Validate template exists and belongs to the organization
        stmt = select(SessionTemplate).where(
            SessionTemplate.id == session_template_id,
            SessionTemplate.organization_id == organization_id,
        )
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            # Raise appropriate error (FastAPI router should catch and return 400/404)
            # For now, raising ValueError which maps to 400 usually,
            # or returning specific exception
            raise ValueError(
                f"""
                Session template {session_template_id} not found or
                not owned by organization"""
            )

        # Generate unique room name
        room_name = generate_room_name()

        # Determine Modality Profile (as string)
        modality_profile_str = str(template.modality_profile)
        # Handle if it's an enum (the SQLA model has generic String type
        # but typed as ModalityProfile)
        # It should come back as string from DB, or Enum if SQLAlchemy converts it.
        # Since ModalityProfile is str-enum, str() creates the value.

        # Prepare metadata for the token
        metadata_dict = {
            "session_template_id": str(session_template_id),
            "organization_id": str(organization_id),
            "user_id": user_id,
            "modality_profile": modality_profile_str,
            "enabled_panels": template.enabled_panels,
        }
        metadata_json = json.dumps(metadata_dict)

        # Token TTL
        ttl = (
            template.max_duration_seconds
            if template.max_duration_seconds
            else settings.LIVEKIT_TOKEN_TTL_SECONDS
        )

        # Generate LiveKit Token
        # Identity: use user_id if provided, else generate one based on room name
        identity = user_id if user_id else f"user_{room_name}"

        token = generate_access_token(
            room_name=room_name,
            identity=identity,
            name=user_id,  # Optional display name
            metadata=metadata_json,
            ttl_seconds=ttl,
        )

        # Calculate absolute expiry time
        token_expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        # Create Session record in DB
        new_session = Session(
            organization_id=organization_id,
            session_template_id=session_template_id,
            user_id=user_id,
            modality_profile=modality_profile_str,
            enabled_panels=template.enabled_panels,
            token_expiry=token_expiry,
            room_name=room_name,
            status="created",  # Initial status
            started_at=None,
            ended_at=None,
        )

        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        return SessionStartResponse(
            session_id=new_session.id,
            room_name=room_name,
            access_token=token,
            livekit_url=settings.LIVEKIT_URL,
            token_expiry=token_expiry,
        )

    @staticmethod
    async def get_session_status(
        db: AsyncSession, session_id: UUID, organization_id: UUID
    ) -> Optional[SessionStatusResponse]:
        """
        Retrieves the status of a specific session.
        """
        stmt = select(Session).where(
            Session.id == session_id, Session.organization_id == organization_id
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        return SessionStatusResponse(
            id=session.id,
            room_name=session.room_name,
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at,
        )

    @staticmethod
    async def list_sessions(
        db: AsyncSession, organization_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[SessionStatusResponse]:
        """
        Lists sessions for an organization.
        """
        stmt = (
            select(Session)
            .where(Session.organization_id == organization_id)
            .order_by(Session.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        sessions = result.scalars().all()

        return [
            SessionStatusResponse(
                id=s.id,
                room_name=s.room_name,
                status=s.status,
                started_at=s.started_at,
                ended_at=s.ended_at,
            )
            for s in sessions
        ]
