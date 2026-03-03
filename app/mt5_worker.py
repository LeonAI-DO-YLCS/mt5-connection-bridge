"""
MT5 Bridge — Single-threaded MT5 worker with request queue.
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


class WorkerState(enum.Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHORIZED = "AUTHORIZED"
    PROCESSING = "PROCESSING"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


_request_queue: queue.Queue[tuple[Callable[..., Any], Future[Any]] | None] = queue.Queue()
_worker_thread: threading.Thread | None = None
_state = WorkerState.DISCONNECTED
_settings: Any | None = None

MAX_RECONNECT_RETRIES = 5
RECONNECT_BASE_DELAY = 1.0
MAX_RECONNECT_DELAY = 30.0


def get_state() -> WorkerState:
    return _state


def get_queue_depth() -> int:
    return _request_queue.qsize()


def submit(fn: Callable[..., Any]) -> Future[Any]:
    fut: Future[Any] = Future()
    _request_queue.put((fn, fut))
    return fut


def start_worker(settings: Any) -> None:
    global _worker_thread, _settings
    _settings = settings
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="mt5-worker")
    _worker_thread.start()
    logger.info("MT5 worker thread started.")


def stop_worker() -> None:
    _request_queue.put(None)
    if _worker_thread is not None:
        _worker_thread.join(timeout=5.0)
    logger.info("MT5 worker thread stopped.")


def _connect() -> bool:
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
        # T030: Invalidate capabilities cache so dashboard gets fresh symbols after reconnect
        try:
            from .routes.broker_capabilities import invalidate_capabilities_cache
            invalidate_capabilities_cache()
        except Exception:
            pass  # Non-critical — cache will expire via TTL if import fails
        return True
    except Exception as exc:
        logger.exception("MT5 connect error: %s", exc)
        _state = WorkerState.ERROR
        return False


def _reconnect() -> bool:
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
    global _state

    if not _connect():
        logger.warning("Initial connection failed — will retry on first request.")

    while True:
        item = _request_queue.get()
        if item is None:
            try:
                import MetaTrader5 as mt5  # type: ignore[import-untyped]

                mt5.shutdown()
            except Exception:
                pass
            _state = WorkerState.DISCONNECTED
            break

        fn, fut = item

        if _state == WorkerState.DISCONNECTED:
            fut.set_exception(ConnectionError("MT5 terminal is DISCONNECTED. Restart bridge or MT5 terminal."))
            continue

        if _state not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
            if not _reconnect():
                fut.set_exception(ConnectionError("MT5 terminal not connected after retries."))
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
