"""Module for cocom database objects"""

import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column

from oms_sensemaking.models.sensemaking import BaseORM
from oms_sensemaking.config import SETTINGS
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, String
from src.oms_sensemaking.models.base import UtcDateTime

class AggressorPortMixin(MappedAsDataclass):
    location: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="POINT", srid=SETTINGS.srid, spatial_index=False, nullable=False),
        nullable=False,
        unique=False,
        comment="Point of the port",
    )
    capco: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=False,
        comment="The polygon of the COCOM.",
    )
    class_iri: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=False,
        comment="The polygon of the COCOM.",
    )
    confidence: Mapped[str] = mapped_column(
        nullable=False,
        unique=False,
        comment="The polygon of the COCOM.",
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=False,
        comment="The polygon of the COCOM.",
    )
    start_time: Mapped[datetime] = mapped_column(
        UtcDateTime,
        nullable=False,
        unique=False,
        comment="The polygon of the COCOM.",
    )
    end_time: Mapped[datetime] = mapped_column(
        UtcDateTime,
        nullable=False,
        unique=False,
        comment="The polygon of the COCOM.",
    )


class AggressorPort(BaseORM, AggressorPortMixin):
    """Model for Storing AGGRESSOR port mapping data"""

    __tablename__: str = "aggressor_ports"

    __table_args__ = (Index("idx_port_nodeId", "nodeId"),)

    id: Mapped[int] = mapped_column(
        sa.Integer(),
        sa.Identity(),
        nullable=False,
        init=False,
        primary_key=True,
        comment="The unique ID of the node representing the port.",
    )
