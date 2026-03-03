from types import SimpleNamespace
from unittest import mock

import pytest

from oms_sensemaking.core.runtime_settings import RuntimeSettings


def test_get_returns_value_from_settings():
    fake_settings = SimpleNamespace(test_key=42)

    with mock.patch("oms_sensemaking.config.SETTINGS", fake_settings):
        rs = RuntimeSettings()
        assert rs.get("test_key") == 42


def test_set_updates_settings_value():
    fake_settings = SimpleNamespace()

    with mock.patch("oms_sensemaking.config.SETTINGS", fake_settings):
        rs = RuntimeSettings()
        rs.set("new_key", 99)

        assert fake_settings.new_key == 99


def test_bulk_set_updates_multiple_values():
    fake_settings = SimpleNamespace()

    with mock.patch("oms_sensemaking.config.SETTINGS", fake_settings):
        rs = RuntimeSettings()
        rs.bulk_set({"a": 1, "b": 2})

        assert fake_settings.a == 1
        assert fake_settings.b == 2


def test_bulk_set_calls_set_for_each_key():
    rs = RuntimeSettings()

    with mock.patch.object(rs, "set") as mock_set:
        rs.bulk_set({"x": 10, "y": 20})

        mock_set.assert_any_call("x", 10)
        mock_set.assert_any_call("y", 20)
        assert mock_set.call_count == 2


def test_get_raises_attribute_error_for_missing_key():
    fake_settings = SimpleNamespace()

    with mock.patch("oms_sensemaking.config.SETTINGS", fake_settings):
        rs = RuntimeSettings()

        with pytest.raises(AttributeError):
            rs.get("missing_key")
