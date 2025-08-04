"""Module for custom logging database objects"""

import uuid

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from sqlalchemy import UUID, Enum, String
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import Mapped, mapped_column

from oms_sensemaking.models.base import (
    BaseORM,
    CreatedAuditMixin,
    SecurityMarkingMixin,
)


class AuditLogError(BaseORM, SecurityMarkingMixin, CreatedAuditMixin):
    id: Mapped[int] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        init=False,
        comment="The unique ID of the Log.",
        default=uuid.uuid4,
    )
    object_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="The unique id of the object in OMS."
    )
    object_type: Mapped[str] = mapped_column(
        Enum(ObjectType), nullable=False, comment="The type of object that the event was triggered on."
    )
    event_type: Mapped[str] = mapped_column(
        Enum(Action), nullable=False, comment="They type of event (e.g. create, update, or delete)."
    )
    module_name: Mapped[str] = mapped_column(String, nullable=False, comment="Name of the producing thread")
    message: Mapped[str] = mapped_column(TEXT, nullable=False, comment="Log message")
    exc_text: Mapped[str | None] = mapped_column(TEXT, nullable=True, comment="Exception text")
    version: Mapped[str] = mapped_column(String, nullable=False, comment="Version of sensemaking")

    __tablename__: str = "audit_log_error"
