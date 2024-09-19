"""Semantic Sensemaker models."""

import uuid
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

    id: UUID4
    version: str
    acm: str
    tags: str
    guideID: str
    name: str
    tier: str
    classIri: str
    className: str
    ifcCodes: str
    allegience: str
    allegienceAor: str
    currentAor: str
    isNo: bool

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