"""Core Sensemaking ORM models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column

from .base import AuditMixin, BaseORM, SecurityMarkingMixin, UtcDateTime


class AlgorithmMixin(MappedAsDataclass):
    """
    Declare Algorithm metadata.

    This class represents metadata about an executed algorithm.
    """

    algorithm_name: Mapped[str] = mapped_column(
        String, nullable=False, comment="The name of the sensemaker that produced the finding."
    )

    algorithm_version: Mapped[str] = mapped_column(String, nullable=False, comment="The version of the sensemaker.")

    algorithm_configuration: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="The configuration that the algorithm was run with."
    )

    executed_at: Mapped[datetime] = mapped_column(
        UtcDateTime, unique=False, nullable=False, comment="The time the algorithm was executed."
    )


class FindingType(enum.Enum):
    """Represents the type of finding."""

    UNKNOWN = "UNKNOWN"
    GEO_COTRAVEL = "GEO_COTRAVEL"
    GEO_LOITER = "GEO_LOITER"
    GEO_SIMILAR_TRACKS = "GEO_SIMILAR_TRACKS"
    INF_HAS_NAME = "INF_HAS_NAME"
    INF_OUT_OF_GARRISON = "INF_OUT_OF_GARRISON"
    INF_INCURSION = "INF_INCURSION"
    RESOLUTION_DUPLICATE = "RESOLUTION_DUPLICATE"
    MIL_SYMBOL_UPDATE = "MIL_SYMBOL_UPDATE"
    COTRAVEL_POTENTIAL_DUPLICATE = "COTRAVEL_POTENTIAL_DUPLICATE"


class FindingMixin(MappedAsDataclass):
    """Declare finding attributes."""

    finding_type: Mapped[FindingType] = mapped_column(
        Enum(FindingType),
        unique=False,
        nullable=False,
        # default=FindingType.UNKNOWN,
        comment="The type of finding being represented.",
    )

    finding_data: Mapped[dict] = mapped_column(JSONB, nullable=False, comment="The results of running a sensemaker.")

    oms_version: Mapped[str] = mapped_column(
        String, nullable=True, comment="The version of ATOMS that the finding was published to."
    )

    published_at: Mapped[datetime] = mapped_column(
        UtcDateTime, unique=False, nullable=True, comment="The time the finding was published."
    )


class Finding(BaseORM, FindingMixin, AlgorithmMixin, SecurityMarkingMixin, AuditMixin):
    """
    Represents a sensemaker finding.

    This model is also a dataclass. The order of the positional parameters in
    the generated ``__init__()`` method are:

      - acm
      - finding_id
      - finding_type
      - finding_data
      - oms_version
      - published_at
      - algorithm_name
      - algorithm_version
      - algorithm_configuration
      - executed_at
    """

    __tablename__: str = "findings"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default_factory=uuid.uuid4,
        comment="A unique identifier for the finding.",
    )
