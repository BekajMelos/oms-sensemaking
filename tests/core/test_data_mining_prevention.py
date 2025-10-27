"""Unit tests for data mining prevention changes."""

import os
from unittest.mock import Mock, patch

import pytest

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.config import Settings


class TestDataMiningPreventionConfig:
    """Test configuration changes for data mining prevention."""

    def test_database_pooling_settings_exist(self):
        """Test that database pooling settings are properly configured."""
        settings = Settings()

        # Check that new pooling settings exist with correct defaults
        assert hasattr(settings, "db_pool_size"), "db_pool_size should exist"
        assert settings.db_pool_size == 10, f"Expected db_pool_size=10, got {settings.db_pool_size}"

        assert hasattr(settings, "db_max_overflow"), "db_max_overflow should exist"
        assert settings.db_max_overflow == 20, f"Expected db_max_overflow=20, got {settings.db_max_overflow}"

        assert hasattr(settings, "db_pool_timeout_seconds"), "db_pool_timeout_seconds should exist"
        assert (
            settings.db_pool_timeout_seconds == 30
        ), f"Expected db_pool_timeout_seconds=30, got {settings.db_pool_timeout_seconds}"

    def test_environment_variable_override(self):
        """Test that environment variables can override default settings."""
        # Test with custom environment variables
        with patch.dict(
            os.environ,
            {
                "DB_POOL_SIZE": "15",
                "DB_MAX_OVERFLOW": "25",
                "DB_POOL_TIMEOUT_SECONDS": "45",
            },
        ):
            settings = Settings()

            assert settings.db_pool_size == 15, f"Expected db_pool_size=15, got {settings.db_pool_size}"
            assert settings.db_max_overflow == 25, f"Expected db_max_overflow=25, got {settings.db_max_overflow}"
            assert (
                settings.db_pool_timeout_seconds == 45
            ), f"Expected db_pool_timeout_seconds=45, got {settings.db_pool_timeout_seconds}"


class TestDatabaseConnectionPooling:
    """Test database connection pooling changes."""

    def test_database_engine_configuration(self):
        """Test that database engine is configured with pooling settings."""
        # Mock settings
        with patch("oms_sensemaking.clients.instances.SETTINGS") as mock_settings:
            mock_settings.db_uri = "postgresql://test:test@localhost:5432/test_db"
            mock_settings.db_ssl = True
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30

            # Mock create_engine to capture the arguments
            with patch("oms_sensemaking.clients.instances.create_engine") as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine

                # Mock scoped_session and sessionmaker
                with (
                    patch("oms_sensemaking.clients.instances.scoped_session") as mock_scoped_session,
                    patch("oms_sensemaking.clients.instances.sessionmaker"),
                ):
                    mock_session = Mock()
                    mock_scoped_session.return_value = mock_session

                    with db_session():
                        pass

                    # Verify create_engine was called with correct arguments
                    mock_create_engine.assert_called_once()
                    call_args = mock_create_engine.call_args

                    # Check the engine arguments
                    assert call_args[0][0] == mock_settings.db_uri, "Database URI should be passed correctly"

                    # Check keyword arguments
                    kwargs = call_args[1]
                    assert kwargs["pool_pre_ping"] is True, "pool_pre_ping should be True"
                    assert kwargs["pool_size"] == 10, f"Expected pool_size=10, got {kwargs.get('pool_size')}"
                    assert kwargs["max_overflow"] == 20, f"Expected max_overflow=20, got {kwargs.get('max_overflow')}"
                    assert kwargs["pool_timeout"] == 30, f"Expected pool_timeout=30, got {kwargs.get('pool_timeout')}"

                    # Check connect_args
                    connect_args = kwargs["connect_args"]
                    assert (
                        connect_args["sslmode"] == "require"
                    ), f"Expected sslmode='require', got {connect_args['sslmode']}"
                    assert (
                        connect_args["options"] == "-c timezone=utc"
                    ), f"Expected options='-c timezone=utc', got {connect_args['options']}"

    @pytest.mark.parametrize(
        "ssl,sslmode,message",
        [
            (True, "require", "SSL should be required when db_ssl=True"),
            (False, "prefer", "SSL should be preferred when db_ssl=False"),
        ],
    )
    def test_ssl_configuration(self, ssl, sslmode, message):
        """Test SSL configuration handling."""
        with patch("oms_sensemaking.clients.instances.SETTINGS") as mock_settings:
            mock_settings.db_uri = "postgresql://test:test@localhost:5432/test_db"
            mock_settings.db_ssl = ssl
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30

            with patch("oms_sensemaking.clients.instances.create_engine") as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine

                with (
                    patch("oms_sensemaking.clients.instances.scoped_session"),
                    patch("oms_sensemaking.clients.instances.sessionmaker"),
                ):
                    with db_session():
                        pass

                    call_args = mock_create_engine.call_args
                    connect_args = call_args[1]["connect_args"]
                    assert connect_args["sslmode"] == sslmode, message
