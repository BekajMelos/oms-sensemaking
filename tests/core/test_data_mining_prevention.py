"""Unit tests for data mining prevention changes."""

import os
from unittest.mock import patch

from oms_sensemaking.clients.instances import db_engine
from oms_sensemaking.config import SETTINGS, Settings


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

    def test_database_engine_pool_configuration(self):
        """Test that database engine pool is configured with correct settings."""
        # Test the actual engine configuration from the real db_engine
        pool = db_engine.pool

        # Verify pool settings
        assert pool._pre_ping is True, "pool_pre_ping should be True"
        assert pool.size() == SETTINGS.db_pool_size, f"Expected pool_size={SETTINGS.db_pool_size}, got {pool.size()}"
        assert (
            pool._max_overflow == SETTINGS.db_max_overflow
        ), f"Expected max_overflow={SETTINGS.db_max_overflow}, got {pool._max_overflow}"
        assert (
            pool._timeout == SETTINGS.db_pool_timeout_seconds
        ), f"Expected pool_timeout={SETTINGS.db_pool_timeout_seconds}, got {pool._timeout}"

    def test_pool_pre_ping_enabled(self):
        """Test that pool_pre_ping is enabled to handle stale connections."""
        # Verify that pool_pre_ping is enabled for connection health checks
        assert db_engine.pool._pre_ping is True, "pool_pre_ping should be enabled"
