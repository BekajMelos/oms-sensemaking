"""Buffer class"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from threading import Event, Lock, Timer
from typing import Any, Callable
from uuid import UUID, uuid4

LOGGER: logging.Logger = logging.getLogger(__name__)


class Buffer:
    """Buffer objects into a list and periodically expire them to execute a callback"""

    def __init__(self, name: str, flush_timer_seconds: float) -> None:
        """
        Create a Buffer

        :param name: Name of this buffer for logging
        :param flush_timer_seconds: How often to flush the buffer in seconds
        :return: None
        """

        self.name = name
        self.flush_timer_seconds = flush_timer_seconds
        self.callback_func: Callable | None = None  # needs to be set later

        self.lock = Lock()
        self.expiration_times: dict[UUID, datetime | None] = {}
        self.id_mapping: dict[UUID, UUID] = defaultdict(uuid4)
        self.object_list_buffer: dict[UUID, list[Any]] = defaultdict(list)
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(flush_timer_seconds, self._flush_buffer)

    def add(self, ref_id: UUID, obj_to_add: Any) -> None:
        """
        Add object to the buffer

        :param ref_id: Initial ID to map list to
        :param obj_to_add: The object itself
        :return: None
        """
        with self.lock:
            list_id = self._get_list_id(ref_id)
            self.expiration_times[list_id] = datetime.now(tz=timezone.utc)
            self.object_list_buffer[list_id].append(obj_to_add)

    def _get_list_id(self, initial_id: UUID) -> UUID:
        """
        Generate a new list id based on given id

        :param initial_id:
        :return: None
        """
        return self.id_mapping.setdefault(initial_id, uuid4())

    def start(self) -> None:
        """Start the buffer thread"""
        self.autoflush_enabled.set()
        self.buffer_autoflush.start()

    def stop(self) -> None:
        """Stop the buffer thread"""
        self.autoflush_enabled.clear()

        if self.buffer_autoflush.is_alive():
            self.buffer_autoflush.cancel()
            self.buffer_autoflush.join()

    def _restart_buffer(self) -> None:
        """Restart the buffer timer function"""
        if self.autoflush_enabled:
            self.buffer_autoflush = Timer(self.flush_timer_seconds, self._flush_buffer)
            self.buffer_autoflush.start()

    def _flush_buffer(self) -> None:
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.info(f"Checking for expired objects in the {self.name}")
        now: datetime = datetime.now(tz=timezone.utc)
        expire_threshold = timedelta(seconds=self.flush_timer_seconds)
        expired_lists = []

        with self.lock:
            # Identify expired lists in thread-safe snapshot
            self.expiration_times = {key: val for key, val in self.expiration_times.items() if val is not None}
            expired_lists = [
                list_id
                for list_id, last_updated_at in self.expiration_times.items()
                if last_updated_at is not None and last_updated_at + expire_threshold < now
            ]

        if expired_lists:
            LOGGER.info("%s Flushing %d expired lists.", self.name, len(expired_lists))

        for list_id in expired_lists:
            # Process expired lists
            self._execute_callback_and_expire(list_id, self.object_list_buffer[list_id])

        self._restart_buffer()

    def _execute_callback_and_expire(self, list_id: UUID, object_list: list) -> None:
        """
        Execute the callback function with the list id and object list

        :param list_id: id of the list to pass to the callback function
        :param object_list: list to pass to the callback function
        :return: None
        """
        try:
            if not callable(self.callback_func):
                raise ValueError("BufferedSensemakerController callback_func must be callable")
            _ = self.callback_func(list_id, object_list)
        except Exception:
            LOGGER.exception("Unexpected error processing buffer %s", list_id)
        finally:
            with self.lock:
                self.expiration_times[list_id] = None
                # Thread-safe cleanup of expired data
                self.object_list_buffer.pop(list_id, None)
                keys_to_delete = [k for k, v in self.id_mapping.items() if v == list_id]
                for k in keys_to_delete:
                    del self.id_mapping[k]
