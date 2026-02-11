from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.exceptions.base import AppException
from app.exceptions.handlers import (
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware.cors import setup_cors
from app.middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Life span context manager for startup and shutdown events.
    """
    # Startup logic here
    setup_logging()

    # Database engine is initialized at module level in app.db.session

    yield

    # Shutdown logic here
    await engine.dispose()
    # If using a global Redis client, close it here. Currently Redis is per-dependency.


def create_app() -> FastAPI:
    """
    Application factory pattern.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        servers=[{"url": "http://localhost:8000"}],  # Adjust based on deployment
        lifespan=lifespan,
    )

    # Middleware Stack
    # Inner-most middleware first (RequestID)
    app.add_middleware(RequestIDMiddleware)

    # Configure CORS
    setup_cors(app)

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    return app


app = create_app()
