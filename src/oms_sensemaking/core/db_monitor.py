"""SQLAlchemy DB monitoring utilities for data-mining prevention and detection.

Implements:
- Slow query logging based on duration threshold.
- Frequency monitoring with warnings when a sliding-window threshold is exceeded.
- Optional logging of executed SQL (parameters redacted by default).
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque

from sqlalchemy import event
from sqlalchemy.engine import Engine

LOGGER: logging.Logger = logging.getLogger(__name__)


class QueryFrequencyWindow:
    """Thread-safe sliding window counter for executed queries."""

    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def add(self, now: float) -> int:
        with self._lock:
            self._timestamps.append(now)
            cutoff = now - self.window_seconds
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            return len(self._timestamps)


class DbMonitor:
    """Attach SQLAlchemy engine listeners for monitoring."""

    _START_TIME_KEY = "_oms_exec_start_time"

    def __init__(
        self,
        engine: Engine,
        *,
        slow_query_threshold_ms: int,
        queries_per_window: int,
        query_window_seconds: int,
        log_sql_parameters: bool,
        enforce_frequency_limit: bool = False,
        throttle_sleep_seconds: int = 1,
        raise_on_exceed: bool = False,
    ) -> None:
        self.engine = engine
        self.slow_query_threshold_ms = max(0, slow_query_threshold_ms)
        self.queries_per_window = max(1, queries_per_window)
        self.window = QueryFrequencyWindow(query_window_seconds)
        self.log_sql_parameters = log_sql_parameters
        self.enforce_frequency_limit = enforce_frequency_limit
        self.throttle_sleep_seconds = max(0, throttle_sleep_seconds)
        self.raise_on_exceed = raise_on_exceed

        event.listen(engine, "before_cursor_execute", self._before_cursor_execute)
        event.listen(engine, "after_cursor_execute", self._after_cursor_execute)

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        now = time.time()
        setattr(context, self._START_TIME_KEY, now)

        count = self.window.add(now)
        if count > self.queries_per_window:
            message = f"DB query frequency exceeded window: count={count} window={self.window.window_seconds}s"
            if self.enforce_frequency_limit:
                if self.raise_on_exceed:
                    LOGGER.error(message)
                    raise RuntimeError("Database query frequency limit exceeded")
                LOGGER.warning("%s; throttling for %ss", message, self.throttle_sleep_seconds)
                if self.throttle_sleep_seconds:
                    time.sleep(self.throttle_sleep_seconds)
            else:
                LOGGER.warning(message)

        if self.log_sql_parameters:
            LOGGER.debug("Executing SQL: %s | params=%s", statement, parameters)
        else:
            LOGGER.debug("Executing SQL: %s | params=REDACTED", statement)

    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        start = getattr(context, self._START_TIME_KEY, None)
        if start is None:
            return
        duration_ms = int((time.time() - start) * 1000)
        if self.slow_query_threshold_ms and duration_ms >= self.slow_query_threshold_ms:
            stmt = statement if len(statement) < 500 else statement[:497] + "..."
            LOGGER.warning(
                "Slow DB query detected: duration_ms=%d threshold_ms=%d sql=%s",
                duration_ms,
                self.slow_query_threshold_ms,
                stmt,
            )


def attach_db_monitor(
    engine: Engine,
    *,
    slow_query_threshold_ms: int,
    queries_per_window: int,
    query_window_seconds: int,
    log_sql_parameters: bool,
    enforce_frequency_limit: bool = False,
    throttle_sleep_seconds: int = 1,
    raise_on_exceed: bool = False,
) -> DbMonitor:
    """Create and attach a DbMonitor to a SQLAlchemy engine."""
    return DbMonitor(
        engine,
        slow_query_threshold_ms=slow_query_threshold_ms,
        queries_per_window=queries_per_window,
        query_window_seconds=query_window_seconds,
        log_sql_parameters=log_sql_parameters,
        enforce_frequency_limit=enforce_frequency_limit,
        throttle_sleep_seconds=throttle_sleep_seconds,
        raise_on_exceed=raise_on_exceed,
    )
