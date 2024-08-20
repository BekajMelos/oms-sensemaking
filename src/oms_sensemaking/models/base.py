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
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, Dialect, MetaData, TypeDecorator, select
from sqlalchemy.orm import ColumnProperty, DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.sql.schema import Column


class Base(DeclarativeBase):
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


class BaseOrm(Base):
    """Base model with columns that are common to all ORM objects."""

    __abstract__ = True

    def to_dict(self, include_relationships: bool = True) -> dict:
        """ORM instance as a dictionary."""
        fields = set()

        for prop in self.__mapper__.iterate_properties:
            if isinstance(prop, ColumnProperty):
                fields.add(prop.columns[0].name)

        if include_relationships:
            fields.update(self.__mapper__.relationships.keys())  # type: ignore

        return {
            field_name: getattr(self, field_name) for field_name in fields
        }

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
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class AuditMixin:
    """Declare audit attributes."""

    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        unique=False,
        nullable=False,
        default=utcnow_with_timezone,
        comment="The time the record was created in the database."
    )

    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        unique=False,
        nullable=False,
        default=utcnow_with_timezone,
        onupdate=utcnow_with_timezone,
        comment="The time the record was last updated."
    )
