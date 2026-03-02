"""
MT5 Bridge — Single-threaded MT5 worker with request queue.

The MetaTrader5 Python API is **not** thread-safe and uses a single global
terminal connection.  This module serialises all MT5 calls through a
dedicated daemon thread that processes a ``queue.Queue``.

Public interface
----------------
- ``start_worker(settings)``  — call once at application startup.
- ``stop_worker()``           — call once at application shutdown.
- ``submit(callable)``        — schedule *callable* on the MT5 thread;
  returns a ``concurrent.futures.Future`` whose result is the callable's
  return value (or its exception).
"""

from __future__ import annotations

import enum
import logging
import queue
import threading
import time
from concurrent.futures import Future
from typing import Any, Callable

logger = logging.getLogger("mt5_worker")

# ---------------------------------------------------------------------------
# Worker state machine
# ---------------------------------------------------------------------------

class WorkerState(enum.Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHORIZED = "AUTHORIZED"
    PROCESSING = "PROCESSING"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


# ---------------------------------------------------------------------------
# Module-level worker state (singleton pattern)
# ---------------------------------------------------------------------------

_request_queue: queue.Queue[tuple[Callable[..., Any], Future[Any]] | None] = queue.Queue()
_worker_thread: threading.Thread | None = None
_state = WorkerState.DISCONNECTED
_settings: Any | None = None  # app.config.Settings instance

MAX_RECONNECT_RETRIES = 5
RECONNECT_BASE_DELAY = 1.0  # seconds
MAX_RECONNECT_DELAY = 30.0  # seconds


def get_state() -> WorkerState:
    """Return the current worker state (thread-safe read)."""
    return _state


def submit(fn: Callable[..., Any]) -> Future[Any]:
    """Schedule *fn* to run on the MT5 worker thread.

    Parameters
    ----------
    fn : callable
        A zero-argument callable that performs an MT5 API operation.

    Returns
    -------
    Future
        Resolves to the return value of *fn*, or raises an exception
        forwarded from the worker thread.
    """
    fut: Future[Any] = Future()
    _request_queue.put((fn, fut))
    return fut


def start_worker(settings: Any) -> None:
    """Initialise the MT5 terminal and start the worker daemon thread."""
    global _worker_thread, _settings
    _settings = settings
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="mt5-worker")
    _worker_thread.start()
    logger.info("MT5 worker thread started.")


def stop_worker() -> None:
    """Signal the worker thread to shut down gracefully."""
    _request_queue.put(None)  # sentinel
    if _worker_thread is not None:
        _worker_thread.join(timeout=5.0)
    logger.info("MT5 worker thread stopped.")


# ---------------------------------------------------------------------------
# Internal worker loop
# ---------------------------------------------------------------------------

def _connect() -> bool:
    """Attempt to initialise and log in to MT5.  Returns True on success."""
    global _state
    _state = WorkerState.CONNECTING
    try:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        init_kwargs: dict[str, Any] = {}
        if _settings and _settings.mt5_path:
            init_kwargs["path"] = _settings.mt5_path

        if not mt5.initialize(**init_kwargs):
            logger.error("mt5.initialize() failed: %s", mt5.last_error())
            _state = WorkerState.ERROR
            return False

        _state = WorkerState.CONNECTED
        logger.info("MT5 terminal connected.")

        # Attempt login if credentials are provided
        if _settings and _settings.mt5_login and _settings.mt5_password:
            if not mt5.login(
                login=_settings.mt5_login,
                password=_settings.mt5_password,
                server=_settings.mt5_server,
            ):
                logger.error("mt5.login() failed: %s", mt5.last_error())
                _state = WorkerState.ERROR
                return False

        _state = WorkerState.AUTHORIZED
        logger.info("MT5 terminal authorised.")
        return True

    except Exception as exc:
        logger.exception("MT5 connect error: %s", exc)
        _state = WorkerState.ERROR
        return False


def _reconnect() -> bool:
    """Exponential-backoff reconnection loop."""
    global _state

    for attempt in range(1, MAX_RECONNECT_RETRIES + 1):
        _state = WorkerState.RECONNECTING
        delay = min(RECONNECT_BASE_DELAY * (2 ** (attempt - 1)), MAX_RECONNECT_DELAY)
        logger.warning("Reconnect attempt %d/%d (delay %.1fs)…", attempt, MAX_RECONNECT_RETRIES, delay)
        time.sleep(delay)

        try:
            import MetaTrader5 as mt5  # type: ignore[import-untyped]
            mt5.shutdown()
        except Exception:
            pass

        if _connect():
            return True

    _state = WorkerState.DISCONNECTED
    logger.error("All reconnection attempts exhausted — worker is DISCONNECTED.")
    return False


def _is_disconnect_error() -> bool:
    """Detect MT5 terminal disconnect conditions from `mt5.last_error()`."""
    try:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        err_code, err_msg = mt5.last_error()
    except Exception:
        return False

    msg = str(err_msg).lower()
    disconnect_markers = ("connect", "connection", "ipc", "terminal", "not initialized")
    disconnected_codes = {-10000, -10001, -10002, -10003, -10004, -10005, -10006}
    if int(err_code) in disconnected_codes:
        return True
    return any(marker in msg for marker in disconnect_markers)


def _worker_loop() -> None:
    """Main loop running on the dedicated worker thread."""
    global _state

    # Initial connection
    if not _connect():
        logger.warning("Initial connection failed — will retry on first request.")

    while True:
        item = _request_queue.get()
        if item is None:
            # Shutdown sentinel
            try:
                import MetaTrader5 as mt5  # type: ignore[import-untyped]
                mt5.shutdown()
            except Exception:
                pass
            _state = WorkerState.DISCONNECTED
            break

        fn, fut = item

        # If disconnected and retries were exhausted previously, fail fast.
        if _state == WorkerState.DISCONNECTED:
            fut.set_exception(ConnectionError("MT5 terminal is DISCONNECTED. Restart bridge or MT5 terminal."))
            continue

        # If not ready, attempt reconnect before processing
        if _state not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
            if not _reconnect():
                fut.set_exception(
                    ConnectionError("MT5 terminal not connected after retries.")
                )
                continue

        _state = WorkerState.PROCESSING
        try:
            result = fn()
            if _is_disconnect_error():
                _state = WorkerState.ERROR
                if not _reconnect():
                    fut.set_exception(ConnectionError("MT5 terminal disconnected and reconnect attempts failed."))
                    continue
                fut.set_exception(ConnectionError("MT5 terminal disconnected during request. Please retry."))
                continue
            fut.set_result(result)
            _state = WorkerState.AUTHORIZED
        except Exception as exc:
            logger.exception("MT5 call failed: %s", exc)
            _state = WorkerState.ERROR
            if not _reconnect():
                fut.set_exception(ConnectionError("MT5 terminal not connected after retries."))
                continue
            fut.set_exception(exc)
