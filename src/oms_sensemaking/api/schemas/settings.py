"""Schemas for settings management."""

from typing import Dict

from pydantic import BaseModel, Field, StrictInt


class SettingsBatchUpdate(BaseModel):
    """Request body for updating/creating multiple settings at once."""

    settings: Dict[str, StrictInt] = Field(
        ..., description="Dictionary of field names to validated integer values (>= 0)"
    )
