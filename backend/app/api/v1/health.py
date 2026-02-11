from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import ping as redis_ping
from app.db.session import get_db
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK, response_model=HealthResponse)
async def health_check():
    """
    Basic liveness check. Returns 200 OK if the service is running.
    """
    return {"status": "ok"}


@router.get(
    "/health/ready", status_code=status.HTTP_200_OK, response_model=ReadinessResponse
)
async def readiness_check(response: Response, db: AsyncSession = Depends(get_db)):
    """
    Readiness check. Verifies connectivity to the database and Redis.
    Returns 503 Service Unavailable if any dependency is down.
    """
    status_data = {
        "status": "ok",
        "database": "connected",
        "redis": "connected",
    }

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        status_data["database"] = "disconnected"
        status_data["status"] = "error"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Check Redis
    try:
        redis_ok = await redis_ping()
        if not redis_ok:
            raise Exception("Redis ping failed")
    except Exception:
        status_data["redis"] = "disconnected"
        status_data["status"] = "error"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return status_data
