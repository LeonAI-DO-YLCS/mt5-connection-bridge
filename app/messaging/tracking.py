"""MT5 Bridge — Tracking ID generation.

Produces unique, human-readable identifiers for incident correlation:
    brg-20260303T094500-a3f7

Format: ``brg-<YYYYMMDDTHHMMSS>-<hex4>``
- Prefix ``brg-`` distinguishes bridge events.
- ISO-8601 compact timestamp gives approximate time context.
- 4-char random hex (65 536 values) ensures uniqueness within a second.
- Total length ≤ 26 characters (always ≤ 30).
- Scoped per bridge runtime session (not globally unique across restarts).
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone


def generate_tracking_id() -> str:
    """Generate a unique tracking ID for a bridge event.

    Returns a string like ``brg-20260303T094500-a3f7``.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    rand = secrets.token_hex(2)  # 4 hex chars
    return f"brg-{ts}-{rand}"
