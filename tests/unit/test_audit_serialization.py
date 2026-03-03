from __future__ import annotations

from types import SimpleNamespace

from app.audit import _to_serializable_payload
from app.models.trade import TradeRequest


def test_to_serializable_payload_none():
    assert _to_serializable_payload(None) == {}


def test_to_serializable_payload_model_dump():
    req = TradeRequest(ticker="V75", action="buy", quantity=0.01, current_price=100.0)
    payload = _to_serializable_payload(req)
    assert payload["ticker"] == "V75"
    assert payload["action"] == "buy"


def test_to_serializable_payload_mapping_and_object():
    mapping_payload = _to_serializable_payload({"foo": "bar"})
    object_payload = _to_serializable_payload(SimpleNamespace(alpha=1, beta=2))
    assert mapping_payload == {"foo": "bar"}
    assert object_payload == {"alpha": 1, "beta": 2}


def test_to_serializable_payload_fallback():
    class NoDict:
        __slots__ = ()

    payload = _to_serializable_payload(NoDict())
    assert "value" in payload
