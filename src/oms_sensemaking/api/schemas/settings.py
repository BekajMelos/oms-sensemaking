"""Schemas for settings management."""

import logging
from typing import Any, Dict

from pydantic import BaseModel, Field, StrictInt, ValidationError, field_validator

LOGGER: logging.Logger = logging.getLogger(__name__)


class Setting(BaseModel):
    """Schema representing a validated single setting."""

    field_name: str = Field(..., examples=["oms_api_call_period_seconds", "maximum_oms_api_calls"])
    field_value: StrictInt = Field(..., ge=0, examples=[10, 20, 30])


class SettingUpdate(Setting):
    """Request body for updating or creating a single setting."""

    pass


class SettingsBatchUpdate(BaseModel):
    """Request body for updating/creating multiple settings at once."""

    settings: Dict[str, StrictInt] = Field(
        ..., description="Dictionary of field names to validated integer values (>= 0)"
    )

    @field_validator("settings")
    @classmethod
    def validate_settings_values(cls, v: Dict[str, StrictInt]) -> Dict[str, StrictInt]:
        """Validate that all setting values are non-negative integers."""
        for field_name, field_value in v.items():
            if field_value < 0:
                raise ValueError(f"Setting '{field_name}' must be a non-negative integer, got {field_value}")
        return v


def validate_setting(input_data: Dict[str, Any]) -> Setting | None:
    """
    Validates raw input data against the Setting schema.
    Returns a valid model instance or None if validation fails.
    """
    try:
        valid_setting = Setting(**input_data)
        return valid_setting
    except ValidationError as e:
        LOGGER.error("Setting Schema validation error: %s", e)
        return None


def get_pydantic_schema() -> Dict[str, Any]:
    """
    Fetches the JSON Schema definition from the Pydantic model.
    """
    return Setting.model_json_schema()
