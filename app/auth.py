"""
MT5 Bridge — API key authentication middleware.

All endpoints require a valid ``X-API-KEY`` header that matches
the ``MT5_BRIDGE_API_KEY`` environment variable.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from .config import get_settings

_api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

# Singleton settings — loaded once on import.
_settings = get_settings()


async def verify_api_key(
    api_key: str | None = Depends(_api_key_header),
) -> str:
    """FastAPI dependency that validates the API key.

    Returns the validated key on success.
    Raises ``HTTPException(401)`` on failure.
    """
    if api_key is None or api_key != _settings.mt5_bridge_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    return api_key
