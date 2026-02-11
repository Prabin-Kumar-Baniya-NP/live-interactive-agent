from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    set_auth_cookies,
)
from app.db.session import get_db
from app.exceptions.base import ForbiddenException, UnauthorizedException
from app.models.user import User
from app.schemas.auth import GenericMessageSchema, LoginSchema, SignupSchema, UserSchema
from app.services.auth import authenticate_user, register_user

router = APIRouter()


@router.post("/signup", response_model=UserSchema)
async def signup(
    user_in: SignupSchema,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    """
    user = await register_user(
        db,
        email=user_in.email,
        password=user_in.password,
        organization_name=user_in.organization_name,
        full_name=user_in.full_name,
    )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    return user


@router.post("/login", response_model=UserSchema)
async def login(
    user_in: LoginSchema,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Login user.
    """
    user = await authenticate_user(db, email=user_in.email, password=user_in.password)

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    return user


@router.post("/refresh", response_model=UserSchema)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token cookie.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedException("Refresh token missing")

    try:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise UnauthorizedException("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid refresh token")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedException("User not found")

        if not user.is_active:
            raise ForbiddenException("Inactive user")

        # Create new tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Set cookies
        set_auth_cookies(response, access_token, new_refresh_token)

        return user
    except Exception:
        raise UnauthorizedException("Invalid refresh token")


@router.post("/logout", response_model=GenericMessageSchema)
async def logout(response: Response):
    """
    Logout user (clear cookies).
    """
    clear_auth_cookies(response)
    return GenericMessageSchema(message="Logged out successfully")


@router.get("/user", response_model=UserSchema)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    """
    return current_user
