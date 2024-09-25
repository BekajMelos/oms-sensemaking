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
    version: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    acm: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
    )
    tags: Mapped[str] = mapped_column( #change to list
        String,
        nullable=False,
        comment='The version of the node associated with this object.'
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
    ifcCodes: Mapped[str] = mapped_column( #change to list
        String,
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

    #id: UUID4 = Field(..., examples=["63a17206-8d4d-4825-9b0e-958cf54fa639"])
    #version: str = Field(..., examples=["test"])
    #acm: str = Field(..., examples=["test"])
    #tags: list[str] = Field(..., examples=[["test", "test2"]])
    #guideID: str = Field(..., examples=["test"])
    #name: str = Field(..., examples=["test"])
    #tier: str = Field(..., examples=["test"])
    #classIri: str = Field(..., examples=["test"])
    #className: str = Field(..., examples=["test"])
    #ifcCodes: list[str] = Field(..., examples=[["test", "test2"]])
    #allegience: str = Field(..., examples=["test"])
    #allegienceAor: str = Field(..., examples=["test"])
    #currentAor: str = Field(..., examples=["test"])
    #isNso: bool = Field(..., examples=[True])

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

    # def __post_init__(self):
    """
        Post initialization.

        This function is responsible for formatting the location field in the
        event that it is set as a string, rather than a specific GeoAlchemy type.
        """
    """
        if isinstance(self.location, str):
            self.location = WKTElement(self.location, srid=SRID)

    def __lt__(self, other: "Node"):
        return self.detection_time < other.detection_time
    """