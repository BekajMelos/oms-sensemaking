"""Base ORM models for oms-sensemaking.

Example ORM model:

    from sqlalchemy import Column, Numeric

    class Location(BaseOrm, AuditMixin):
        __tablename__: str = 'locations'

        latitude = Column(Numeric, nullable=False, comment='latitude')
        longitude = Column(Numeric, nullable=False, comment='longitude')


To generate a migration for a new model or other ORM updates:

    alembic revision --autogenerate --rev-id $(date +%Y%m%d%H%M) -m "short description of the change."
"""
import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, Dialect, Integer, MetaData, TypeDecorator, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, Session, mapped_column
from sqlalchemy.sql.expression import ClauseElement


class BaseORM(MappedAsDataclass, DeclarativeBase):
    """Base class for all ORM models."""

    metadata = MetaData(
        # handle index naming conventions
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s'
        }
    )

    @classmethod
    def get_or_create(cls, session: Session, defaults: Optional[dict] = None, **kwargs):
        """
        Get an instance of the class or create a new one using the provided arguments.

        @see https://stackoverflow.com/a/2587041
        :param session: A database session.
        :param defaults: Default values used if a new object is created.
        :param kwargs: parameters used to query for the object.
        :return: A tuple containing an instance and a boolean flag indicating if the
                 instance was created as part of the call to this function.
        """
        # 1. find the model, if it exists
        instance = session.execute(select(cls).filter_by(**kwargs)).scalars().one_or_none()

        if instance:
            return instance, False

        # 2. it does not exist, so create it
        params = {key: val for key, val in kwargs.items() if not isinstance(val, ClauseElement)}
        params.update(defaults or {})
        instance = cls(**params)

        try:
            session.add(instance)
            session.commit()
        except Exception:
            session.rollback()
            instance = session.execute(select(cls).filter_by(**kwargs)).scalars().one()
            return instance, False
        else:
            return instance, True

    def to_dict(self) -> dict:
        """Return a dictionary representation of the object."""
        return asdict(self)

    def to_json(self) -> str:
        """Return a JSON string representation of the object."""
        return json.dumps(self.to_dict())


class UtcDateTime(TypeDecorator):
    """
    Represents a Custom DateTime to ensure timestamps are stored as UTC.

    NOTE: This class clashes with mypy.

    @see https://github.com/dropbox/sqlalchemy-stubs/issues/205
    @see https://docs.sqlalchemy.org/en/20/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc
    """

    impl = DateTime
    cache_ok = True

    @property
    def python_type(self):
        """Returns the Python type."""
        return datetime

    def process_bind_param(self, value: Optional[Any], dialect: Dialect) -> datetime:
        """
        Convert the value to UTC and strip the timezone information.

        This function will raise a TypeError if value is not timezone aware.

        :param value: The inbound datetime object.
        :param dialect: The dialect in use.
        :raises TypeError: if the value is not timezone aware.
        """
        if value is not None:
            if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
                raise TypeError('tzinfo is required')

            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        return value

    def process_result_value(self, value: Optional[Any], dialect: Dialect) -> datetime:
        """
        Ensure the return value is timezone aware.

        Since the value is stored as UTC, the returned value will have tzinfo set to UTC.

        :param value: The inbound datetime object.
        :param dialect: The dialect in use.
        """
        if value is not None:
            value = value.replace(tzinfo=timezone.utc)

        return value

    def process_literal_param(self, value, dialect) -> Optional[str]:  # type: ignore
        """
        Return the literal datetime value formatted as ISO 8601 timestamp.

        :param value: The inbound datetime object.
        :param dialect: The dialect in use.
        """
        if value is not None:
            return value.isoformat()

        return value


def utcnow_with_timezone() -> datetime:
    """Return a timezone aware UTC datetime for the current time."""
    return datetime.now(timezone.utc)


class AuditMixin(MappedAsDataclass):
    """Declare audit attributes."""

    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        unique=False,
        nullable=False,
        insert_default=utcnow_with_timezone,
        comment="The time the record was created in the database.",
        init=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        unique=False,
        nullable=False,
        insert_default=utcnow_with_timezone,
        onupdate=utcnow_with_timezone,
        comment="The time the record was last updated.",
        init=False
    )


class SecurityMarkingMixin(MappedAsDataclass):
    """Declare security marking attributes."""

    acm: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment='The ACM representing the classification of the data.'
    )

class OmsBaseObjectMixin(MappedAsDataclass):
    """Declare Common OMS Object Metadata."""
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment='The ID of the node associated with the object.'
    )

    node_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='The version of the node associated with this object.'
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment='The ID of the source associated with the object.'
    )

class OmsAttributeMixin(OmsBaseObjectMixin, MappedAsDataclass):
    """Declare OMS Attribute Metdata."""

    attribute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment='The ID of the attribute associated with the object.'
    )

    attribute_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='The version of the attribute associated with the object.'
    )

class OmsObservationMixin(OmsBaseObjectMixin, MappedAsDataclass):
    """Declare OMS Observation Metadata."""

    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment='The ID of the observation associated with the object.'
    )

    observation_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='The version of the observation associated with the object.'
    )

class TrackMixin(MappedAsDataclass):
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        comment="The ID of the track associated with the object."
    )
