"""Schemas for settings management."""

from typing import Any, Dict

from pydantic import BaseModel


class SettingUpdate(BaseModel):
    """Model for updating a setting."""

    field_name: str
    field_value: Any


class SettingsUpdate(BaseModel):
    """Model for updating multiple settings."""

    settings: Dict[str, Any]
