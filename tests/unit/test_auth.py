from __future__ import annotations

import pytest

from app.auth import verify_api_key


@pytest.mark.asyncio
async def test_verify_api_key_accepts_valid(monkeypatch):
    from app import auth

    auth._settings.mt5_bridge_api_key = "abc"
    assert await verify_api_key("abc") == "abc"


@pytest.mark.asyncio
async def test_verify_api_key_rejects_invalid(monkeypatch):
    from app import auth

    auth._settings.mt5_bridge_api_key = "abc"
    with pytest.raises(Exception):
        await verify_api_key("wrong")
