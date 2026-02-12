"""Module for custom settings database objects"""

from typing import Any

import sqlalchemy as sa
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column

from oms_sensemaking.models.base import BaseORM


class SettingsMixin(MappedAsDataclass):
    """Declare settings attributes."""

    field_name: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, comment="Name of the field for the setting."
    )

    field_value: Mapped[Any] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=False,
        comment="The value of the field, stored as JSONB to preserve data type integrity.",
    )


class Setting(BaseORM, SettingsMixin):
    """Model for Storing Setting data"""

    __tablename__: str = "settings"

    setting_id: Mapped[int] = mapped_column(
        sa.Integer(),
        sa.Identity(),
        nullable=False,
        init=False,
        primary_key=True,
        comment="The unique ID of the setting.",
    )
