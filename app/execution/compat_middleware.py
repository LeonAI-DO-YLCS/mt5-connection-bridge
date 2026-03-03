"""HTTP compatibility middleware for business failure responses.

When STRICT_HTTP_SEMANTICS is False (default / compatibility mode),
trade-affecting routes that return 4xx for business failures are
rewritten to HTTP 200 with deprecation headers (FR-014 through FR-016).

When STRICT_HTTP_SEMANTICS is True (strict mode), responses pass through
unchanged (FR-013).
"""

from __future__ import annotations

import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mt5_bridge.execution.compat_middleware")

# Routes that are trade-affecting and subject to compatibility rewriting.
_TRADE_ROUTES = frozenset({
    "/execute",
    "/pending-order",
    "/close-position",
})

# Route prefixes for parameterized trade-affecting routes.
_TRADE_ROUTE_PREFIXES = (
    "/orders/",
    "/positions/",
)


def _is_trade_route(path: str) -> bool:
    """Check if the request path is a trade-affecting route."""
    if path in _TRADE_ROUTES:
        return True
    return any(path.startswith(p) for p in _TRADE_ROUTE_PREFIXES)


class CompatibilityMiddleware(BaseHTTPMiddleware):
    """Rewrite 4xx business-failure responses to HTTP 200 in compat mode."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Only rewrite trade-affecting routes.
        if not _is_trade_route(request.url.path):
            return response

        # FR-015: Check env var per request (runtime-switchable, no restart).
        strict = os.getenv("STRICT_HTTP_SEMANTICS", "false").lower() in ("true", "1", "yes")

        if strict:
            return response

        # In compatibility mode, rewrite 4xx to 200 and add deprecation headers.
        if 400 <= response.status_code < 500:
            # Read the original body.
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            logger.debug(
                "Compat rewrite: %s %s %d → 200",
                request.method,
                request.url.path,
                response.status_code,
            )

            # Build new response with HTTP 200 but original body preserved.
            new_response = Response(
                content=body,
                status_code=200,
                media_type=response.media_type,
            )
            # Copy original headers.
            for key, value in response.headers.items():
                if key.lower() not in ("content-length", "content-encoding"):
                    new_response.headers[key] = value
            # FR-016: Add deprecation signal.
            new_response.headers["Deprecation"] = "true"
            new_response.headers["X-Bridge-Strict-After"] = "2026-06-01"
            new_response.headers["X-Original-Status"] = str(response.status_code)
            return new_response

        return response
