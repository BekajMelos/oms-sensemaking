"""Semantic Sensemaker models."""

import uuid

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    mapped_column,
)

from src.oms_sensemaking.api.schemas.oms import ObjectTier

from .base import AuditMixin, BaseORM, SecurityMarkingMixin


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
        comment='The acm of the node.'
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment='A tags of the node.'
    )
    guideID: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The guideID of the node.'
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The name of the node.'
    )
    tier: Mapped[ObjectTier] = mapped_column(
        Enum(ObjectTier),
        nullable=False,
        comment='The tier of the node.'
    )
    classIri: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The classIri of the node.'
    )
    className: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The className of the node.'
    )
    ifcCodes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment='The ifcCodes of the node.'
    )
    allegiance: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The allegiance of the node.'
    )
    allegianceAor: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The allegianceAor of the node.'
    )
    currentAor: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='The currentAor of the node.'
    )
    isNso: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment='The isNso of the node (boolean).'
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
