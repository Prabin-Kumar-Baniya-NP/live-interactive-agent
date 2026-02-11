from typing import Callable

from fastapi import Depends

from app.core.security import get_current_user
from app.exceptions.base import ForbiddenException
from app.models.user import User


def require_role(required_role: str) -> Callable:
    """
    Dependency to require a specific role.
    Roles: admin > member
    """

    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == "admin":
            return current_user  # Admin has access to everything

        if required_role == "admin" and current_user.role != "admin":
            raise ForbiddenException("Insufficient permissions")

        return current_user

    return check_role


require_admin = require_role("admin")
require_member = require_role("member")
