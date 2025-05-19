"""Module for custom logging database objects"""

import enum
import logging
import uuid
from datetime import datetime

from sqlalchemy import UUID, Enum, String
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import Mapped, mapped_column

from oms_sensemaking.models.base import (
    BaseORM,
    CreatedAuditMixin,
    SecurityMarkingMixin,
    UtcDateTime,
    utcnow_with_timezone,
)


class LogLevel(enum.Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogRecord(BaseORM, SecurityMarkingMixin, CreatedAuditMixin):

    __tablename__: str = "log_record"

    log_id: Mapped[int] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        init=False,
        comment="The unique ID of the Log.",
        default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        UtcDateTime,
        unique=False,
        nullable=False,
        insert_default=utcnow_with_timezone,
        comment="The time the log occurred.",
    )
    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), nullable=False, comment="Log Record Level")
    module_name: Mapped[str] = mapped_column(String, nullable=False, comment="Name of the producing thread")
    message: Mapped[str] = mapped_column(TEXT, nullable=False, comment="Log message")
    exc_text: Mapped[str] = mapped_column(TEXT, nullable=True, comment="Exception text")
