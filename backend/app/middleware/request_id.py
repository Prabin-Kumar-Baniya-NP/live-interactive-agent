import uuid
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Global context var for accessing request_id in logging
REQUEST_ID_CTX_KEY = "request_id"
request_id_ctx: ContextVar[str] = ContextVar(REQUEST_ID_CTX_KEY, default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())

        # Set context var for structured logging (Task 4.6)
        token = request_id_ctx.set(request_id)

        # Store in request state for convenient access
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)
