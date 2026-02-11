from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import NotFoundException
from app.models.organization import Organization
from app.models.user import User


async def get_organization(db: AsyncSession, org_id: UUID) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundException("Organization not found")
    return org


async def update_organization(
    db: AsyncSession, org_id: UUID, name: str
) -> Organization:
    org = await get_organization(db, org_id)
    org.name = name
    await db.commit()
    await db.refresh(org)
    return org


async def get_organization_members(db: AsyncSession, org_id: UUID) -> list[User]:
    # Verify org exists
    await get_organization(db, org_id)

    result = await db.execute(select(User).where(User.organization_id == org_id))
    return list(result.scalars().all())
