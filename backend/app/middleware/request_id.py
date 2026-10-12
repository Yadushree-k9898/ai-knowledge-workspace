"""
Request ID middleware.

Assigns a unique request ID to every incoming request so that logs
and error responses can be correlated.  The ID is:
  1. Read from the incoming X-Request-ID header (if the caller supplies one), or
  2. Generated as a new UUID4.

The ID is then:
  - Stored in request.state.request_id for use in endpoint code
  - Returned in the X-Request-ID response header
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Accept an externally-provided ID, or generate one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
