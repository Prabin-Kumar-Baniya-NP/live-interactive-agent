from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.db.session import get_db
from app.exceptions.base import NotFoundException
from app.models.user import User
from app.schemas.session_template import (
    SessionTemplateCreate,
    SessionTemplateRead,
    SessionTemplateUpdate,
)
from app.services.session_template import (
    clone_session_template,
    create_session_template,
    delete_session_template,
    get_session_template,
    list_session_templates,
    update_session_template,
)

router = APIRouter()


@router.post(
    "/", response_model=SessionTemplateRead, status_code=status.HTTP_201_CREATED
)
async def create_session_template_endpoint(
    data: SessionTemplateCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new session template. Admin only.
    """
    try:
        return await create_session_template(db, current_user.organization_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[SessionTemplateRead])
async def list_session_templates_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all session templates for the current organization.
    """
    return await list_session_templates(db, current_user.organization_id)


@router.get("/{template_id}", response_model=SessionTemplateRead)
async def get_session_template_endpoint(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific session template by ID.
    """
    try:
        return await get_session_template(db, template_id, current_user.organization_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{template_id}", response_model=SessionTemplateRead)
async def update_session_template_endpoint(
    template_id: UUID,
    data: SessionTemplateUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a session template. Admin only.
    """
    try:
        return await update_session_template(
            db, template_id, current_user.organization_id, data
        )
    except (NotFoundException, ValueError) as e:
        status_code = 404 if isinstance(e, NotFoundException) else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_template_endpoint(
    template_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete a session template. Admin only.
    """
    try:
        await delete_session_template(db, template_id, current_user.organization_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{template_id}/clone",
    response_model=SessionTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def clone_session_template_endpoint(
    template_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Clone an existing session template. Admin only.
    """
    try:
        return await clone_session_template(
            db, template_id, current_user.organization_id
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
