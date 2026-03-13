from __future__ import annotations

import pytest

from app.auth import verify_api_key


@pytest.mark.asyncio
async def test_verify_api_key_accepts_valid(monkeypatch):
    from app import auth

    original = auth._settings.mt5_bridge_api_key
    auth._settings.mt5_bridge_api_key = "abc"
    try:
        assert await verify_api_key("abc") == "abc"
    finally:
        auth._settings.mt5_bridge_api_key = original


@pytest.mark.asyncio
async def test_verify_api_key_rejects_invalid(monkeypatch):
    from app import auth

    original = auth._settings.mt5_bridge_api_key
    auth._settings.mt5_bridge_api_key = "abc"
    try:
        with pytest.raises(Exception):
            await verify_api_key("wrong")
    finally:
        auth._settings.mt5_bridge_api_key = original
