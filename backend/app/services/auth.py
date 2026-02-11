from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.exceptions.base import BadRequestException, ForbiddenException
from app.models.organization import Organization
from app.models.user import User


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    organization_name: str,
    full_name: str | None = None,
) -> User:
    # Check for existing user
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise BadRequestException(f"User with email {email} already exists")

    # Create organization
    org = Organization(name=organization_name)
    db.add(org)
    await db.flush()  # flush to get org.id

    # Create user
    hashed_pwd = hash_password(password)
    user = User(
        email=email,
        hashed_password=hashed_pwd,
        full_name=full_name,
        organization_id=org.id,
        role="admin",  # First user is admin
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    # Fetch user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise BadRequestException("Invalid credentials")

    if not verify_password(password, user.hashed_password):
        raise BadRequestException("Invalid credentials")

    if not user.is_active:
        raise ForbiddenException("Account is disabled")

    return user
