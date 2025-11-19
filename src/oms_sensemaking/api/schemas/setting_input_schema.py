"""Schemas representing settings."""

import logging
from typing import Any, Dict

from pydantic import BaseModel, Field, StrictInt, ValidationError

LOGGER: logging.Logger = logging.getLogger(__name__)


class SettingInputSchema(BaseModel):
    """Provides setting schema."""

    field_name: str = Field(..., examples=["max_retries", "session_timeout_seconds"])
    # Narrow scope of field_value to integer type for now.
    field_value: StrictInt = Field(..., ge=0, examples=[10, 20, 30])


# The "validation function" is simply the act of instantiating the model.
# Pydantic's __init__ method handles all the validation logic.


def validate_setting(input_data: Dict[str, Any]) -> SettingInputSchema | None:
    """
    Validates raw input data against the SettingInputSchema.
    Returns a valid model instance or None if validation fails.
    """
    try:
        valid_setting = SettingInputSchema(**input_data)
        return valid_setting

    except ValidationError as e:
        logging.error(f"Setting Schema validation error: {e}")
        return None


def get_pydantic_schema() -> Dict[str, Any]:
    """
    Fetches the JSON Schema definition from the Pydantic model.
    """
    # .model_json_schema() generates the schema as a dictionary
    return SettingInputSchema.model_json_schema()
