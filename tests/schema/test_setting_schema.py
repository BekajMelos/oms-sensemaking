"""Test Setting Schema Validation"""

from oms_sensemaking.api.schemas.setting_input_schema import get_pydantic_schema, validate_setting


def test_valid_setting():
    valid_data = {"field_name": "some_throttling_name", "field_value": 20}
    valid_result = validate_setting(valid_data)

    assert valid_result is not None


def test_invalid_setting_field_name():
    invalid_data = {"field_name": 23, "field_value": 32}
    invalid_result = validate_setting(invalid_data)

    assert invalid_result is None


def test_invalid_setting_field_value():
    invalid_data = {"field_name": "some_throttling_name", "field_value": "23"}
    invalid_result = validate_setting(invalid_data)

    assert invalid_result is None


def test_invalid_negative_field_value():
    invalid_data = {"field_name": "some_throttling_name", "field_value": -4}
    invalid_result = validate_setting(invalid_data)

    assert invalid_result is None


def test_invalid_setting_both():
    invalid_data = {"field_name": 234, "field_value": "adsdf"}
    invalid_result = validate_setting(invalid_data)

    assert invalid_result is None


def test_get_schema():
    """
    Tests that the get_pydantic_schema() function returns the
    correct JSON schema as a dictionary.
    """

    # Define the expected schema as a Python dictionary
    expected_schema = {
        "description": "Provides setting schema.",
        "properties": {
            "field_name": {
                "examples": ["max_retries", "session_timeout_seconds"],
                "title": "Field Name",
                "type": "string",
            },
            "field_value": {"examples": [10, 20, 30], "minimum": 0, "title": "Field Value", "type": "integer"},
        },
        "required": ["field_name", "field_value"],
        "title": "SettingInputSchema",
        "type": "object",
    }

    schema = get_pydantic_schema()
    assert schema == expected_schema
