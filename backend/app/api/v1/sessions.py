from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.session import (
    SessionStartRequest,
    SessionStartResponse,
    SessionStatusResponse,
)
from app.services.session_service import SessionService

router = APIRouter()


@router.post(
    "/start",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new agent session",
    description="Generates a LiveKit JWT and creates a session record.",
)
async def start_session(
    data: SessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await SessionService.create_session(
            db=db,
            session_template_id=data.session_template_id,
            organization_id=current_user.organization_id,
            user_id=data.user_id,
        )
    except ValueError as e:
        # Typically maps to 404 or 400 depending on cause
        # (template not found vs bad input)
        # Assuming 404 if template not found, or 400
        # if validation fails.
        # For now, 400 with detail is safe.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=List[SessionStatusResponse],
    summary="List sessions",
    description="List all sessions for the current organization.",
)
async def list_sessions_endpoint(
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.list_sessions(
        db=db, organization_id=current_user.organization_id, limit=limit, offset=offset
    )


@router.get(
    "/{session_id}",
    response_model=SessionStatusResponse,
    summary="Get session status",
    description="Returns the status of a specific session.",
)
async def get_session_endpoint(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await SessionService.get_session_status(
        db=db, session_id=session_id, organization_id=current_user.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return session
