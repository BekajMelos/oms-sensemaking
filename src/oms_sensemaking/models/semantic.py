"""Semantic Sensemaker models."""

import uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import DateTime, Dialect, Integer, String, Boolean, MetaData, TypeDecorator, select
from pydantic import UUID4, BaseModel, Field, field_serializer
from .base import AuditMixin, BaseORM, OmsAttributeMixin, SecurityMarkingMixin, UtcDateTime
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    Session,
    declared_attr,
    mapped_column,
    query_expression,
    with_expression,
)

class OmsNodeMixin(MappedAsDataclass):

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment='The ID of the node associated with the object.'
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    acm: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment='A list of tags.'
    )
    guideID: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    tier: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    classIri: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    className: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    ifcCodes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    allegiance: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    allegianceAor: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    currentAor: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    isNso: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment='The version of the node associated with this object.'
    )

class Node(BaseORM, OmsNodeMixin, SecurityMarkingMixin, AuditMixin): #add UtcDateTime if necessary
    """
    Represents a node in OMS.

    This model is also a dataclass. The order of the positional parameters in
    the generated ``__init__()`` method are:

    - id
    - version
    - acm
    - tags
    - guideID
    - name
    - tier
    - classIri
    - className
    - ifcCodes
    - allegiance
    - allegianceAor
    - currentAor
    - isNso
    """

    __tablename__: str = 'nodes'
