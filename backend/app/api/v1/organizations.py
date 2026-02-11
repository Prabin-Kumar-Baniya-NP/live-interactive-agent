from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.organization import (
    MemberSchema,
    OrganizationSchema,
    OrganizationUpdateSchema,
)
from app.services.organization import (
    get_organization,
    get_organization_members,
    update_organization,
)

router = APIRouter()


@router.get("/", response_model=OrganizationSchema)
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's organization.
    """
    return await get_organization(db, current_user.organization_id)


@router.put("/", response_model=OrganizationSchema)
async def update_current_organization(
    org_in: OrganizationUpdateSchema,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user's organization name (Admin only).
    """
    return await update_organization(db, current_user.organization_id, name=org_in.name)


@router.get("/members", response_model=List[MemberSchema])
async def list_organization_members(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List members of current user's organization (Admin only).
    """
    return await get_organization_members(db, current_user.organization_id)
