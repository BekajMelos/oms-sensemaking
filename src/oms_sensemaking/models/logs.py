"""Module for custom logging database objects"""

import uuid

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from sqlalchemy import UUID, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from oms_sensemaking.models.base import (
    BaseORM,
    CreatedAuditMixin,
    SecurityMarkingMixin,
)


class AuditLogError(BaseORM, SecurityMarkingMixin, CreatedAuditMixin):
    """Model for Storing Audit Log Error data"""

    id: Mapped[int] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        init=False,
        comment="The unique ID of the Log.",
        insert_default=uuid.uuid4,
    )
    object_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="The unique id of the object in ATOMS."
    )
    object_type: Mapped[str] = mapped_column(
        Enum(ObjectType), nullable=False, comment="The type of object that the event was triggered on."
    )
    event_type: Mapped[str] = mapped_column(
        Enum(Action), nullable=False, comment="They type of event (e.g. create, update, or delete)."
    )
    module_name: Mapped[str] = mapped_column(String, nullable=False, comment="Name of the producing module.")
    line_no: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="Line number where the error occurred")
    function_name: Mapped[str] = mapped_column(String, nullable=False, comment="Function name where the error occurred")
    code: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Code where the error occurred")
    exception_name: Mapped[str | None] = mapped_column(
        String, nullable=False, comment="Name of the exception that occurred."
    )
    version: Mapped[str] = mapped_column(String, nullable=False, comment="Version of sensemaking")
    message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Log message")
    exc_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Exception text")

    __tablename__: str = "audit_log_error"
