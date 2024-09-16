"""Semantic Sensemaker models."""


from .base import AuditMixin, BaseORM, OmsAttributeMixin, SecurityMarkingMixin, UtcDateTime


class Node(BaseORM, OmsAttributeMixin, SecurityMarkingMixin, AuditMixin): #add UtcDateTime if necessary
    """
    Represents a node in OMS.

    This model is also a dataclass. The order of the positional parameters in
    the generated ``__init__()`` method are:

    - node_id
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