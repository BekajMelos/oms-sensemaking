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
        comment='ID (primary key)'
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='version'
    )
    acm: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment='acm'
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment='tags'
    )
    guide_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='guideID'
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='name'
    )
    tier: Mapped[ObjectTier] = mapped_column(
        Enum(ObjectTier),
        nullable=False,
        comment='tier'
    )
    class_iri: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='classIri'
    )
    class_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='className'
    )
    ifc_codes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment='ifcCodes'
    )
    allegiance: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='allegiance'
    )
    allegiance_aor: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='allegianceAor'
    )
    current_aor: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='currentAor'
    )
    is_nso: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment='isNso (boolean)'
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
    - guide_id
    - name
    - tier
    - class_iri
    - class_name
    - ifc_codes
    - allegiance
    - allegiance_aor
    - current_aor
    - is_nso
    """

    __tablename__: str = 'nodes'
