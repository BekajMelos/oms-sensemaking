"""Abstract base class for metrics publishers."""

import time
from abc import ABC, abstractmethod
from typing import Optional

from .telemetry import get_current_trace_id


class MetricsPublisher(ABC):
    """Contract for metrics backends: subclass this, implement abstract hooks, inherit completion helpers."""

    def __init__(self, app_name: str):
        self.app_name = app_name

    @abstractmethod
    def record_request(self, method: str, path: str, status_code: int, duration: float) -> None:
        """Record request metrics in backend-specific storage."""
        pass

    @abstractmethod
    def record_queue_processing_time(self, queue_name: str, processing_time_seconds: float) -> None:
        """Record queue processing time in backend-specific storage."""
        pass

    @abstractmethod
    def record_event_processed(self, queue_name: str) -> None:
        """Record successful event count in backend-specific storage."""
        pass

    @abstractmethod
    def record_event_failed(self, queue_name: str) -> None:
        """Record failed event count in backend-specific storage."""
        pass

    def record_processing_completion(self, queue_name: str, start_time: float, success: bool = True) -> None:
        """Generic completion recording used by all publisher implementations."""
        processing_time = time.time() - start_time
        self.record_queue_processing_time(queue_name, processing_time)

        if success:
            self.record_event_processed(queue_name)
        else:
            self.record_event_failed(queue_name)

    def record_processing_success(self, queue_name: str, start_time: float) -> None:
        """Generic helper for successful completion."""
        self.record_processing_completion(queue_name, start_time, success=True)

    def record_processing_failure(self, queue_name: str, start_time: float) -> None:
        """Generic helper for failed completion."""
        self.record_processing_completion(queue_name, start_time, success=False)

    def _get_trace_exemplar(self) -> Optional[dict]:
        """Generic helper for trace exemplar construction."""
        trace_id = get_current_trace_id()
        return {"TraceID": trace_id} if trace_id else None
