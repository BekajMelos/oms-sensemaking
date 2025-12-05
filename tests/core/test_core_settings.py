"""Test DB Logging"""

from unittest import mock

from sqlalchemy.orm import Session

from oms_sensemaking.core.settings import Settings
from oms_sensemaking.models.settings import Setting


@mock.patch("oms_sensemaking.core.settings.db_session")
def test_db_get_settings(mock_db_session: Session):
    """Test get_settings function DB"""

    mock_data = [
        Setting("test_bool", False),
        Setting("test_int", 1),
        Setting("test_string", "adjfadsi"),
        Setting("test_object", {"primary": 1, "secondary": False}),
    ]

    expected_output = {
        "test_bool": False,
        "test_int": 1,
        "test_string": "adjfadsi",
        "test_object": {"primary": 1, "secondary": False},
    }

    mock_db_session_instance = mock.MagicMock()
    mock_db_session_instance.execute.return_value.scalars.return_value.all.return_value = mock_data
    mock_db_session.return_value.__enter__.return_value = mock_db_session_instance

    results = Settings().get_settings()
    assert expected_output == results
