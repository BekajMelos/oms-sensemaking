"""Unit tests for data mining prevention changes."""

import os
from unittest.mock import Mock, patch

import pytest
from oms_sdk.generated.generated_graphql_client import (
    ActivityQuery,
    AttributeQuery,
    NodeQuery,
    ObservationQuery,
    PageParams,
    RelationshipQuery,
)

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.config import Settings
from oms_sensemaking.core.oms_crud import OmsCrudTool


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

    def test_graphql_pagination_settings_exist(self):
        """Test that GraphQL pagination settings are properly configured."""
        settings = Settings()

        # Check pagination settings exist with correct defaults
        assert hasattr(settings, "enforce_graphql_pagination"), "enforce_graphql_pagination should exist"
        assert (
            settings.enforce_graphql_pagination is True
        ), f"Expected enforce_graphql_pagination=True, got {settings.enforce_graphql_pagination}"

        assert hasattr(settings, "graphql_default_page_size"), "graphql_default_page_size should exist"
        assert (
            settings.graphql_default_page_size == 200
        ), f"Expected graphql_default_page_size=200, got {settings.graphql_default_page_size}"

        assert hasattr(settings, "graphql_max_page_size"), "graphql_max_page_size should exist"
        assert (
            settings.graphql_max_page_size == 500
        ), f"Expected graphql_max_page_size=500, got {settings.graphql_max_page_size}"

    def test_environment_variable_override(self):
        """Test that environment variables can override default settings."""
        # Test with custom environment variables
        with patch.dict(
            os.environ,
            {
                "DB_POOL_SIZE": "15",
                "DB_MAX_OVERFLOW": "25",
                "DB_POOL_TIMEOUT_SECONDS": "45",
                "ENFORCE_GRAPHQL_PAGINATION": "false",
                "GRAPHQL_DEFAULT_PAGE_SIZE": "100",
                "GRAPHQL_MAX_PAGE_SIZE": "1000",
            },
        ):
            settings = Settings()

            assert settings.db_pool_size == 15, f"Expected db_pool_size=15, got {settings.db_pool_size}"
            assert settings.db_max_overflow == 25, f"Expected db_max_overflow=25, got {settings.db_max_overflow}"
            assert (
                settings.db_pool_timeout_seconds == 45
            ), f"Expected db_pool_timeout_seconds=45, got {settings.db_pool_timeout_seconds}"
            assert (
                settings.enforce_graphql_pagination is False
            ), f"Expected enforce_graphql_pagination=False, got {settings.enforce_graphql_pagination}"
            assert (
                settings.graphql_default_page_size == 100
            ), f"Expected graphql_default_page_size=100, got {settings.graphql_default_page_size}"
            assert (
                settings.graphql_max_page_size == 1000
            ), f"Expected graphql_max_page_size=1000, got {settings.graphql_max_page_size}"


class TestGraphQLPaginationEnforcement:
    """Test GraphQL pagination enforcement in OmsCrudTool."""

    @pytest.fixture
    def mock_crud_tool(self):
        """Create a mock OmsCrudTool for testing."""
        with patch("oms_sensemaking.core.oms_crud.get_generated_graphql_client") as mock_client:
            mock_client.return_value = Mock()
            return OmsCrudTool()

    def test_pagination_enforcement_enabled(self, mock_crud_tool):
        """Test pagination enforcement when enabled."""
        # Mock settings to enable pagination
        with patch("oms_sensemaking.core.oms_crud.SETTINGS") as mock_settings:
            mock_settings.enforce_graphql_pagination = True
            mock_settings.graphql_default_page_size = 200
            mock_settings.graphql_max_page_size = 500

            # Test get_nodes with no page params
            node_query = NodeQuery()
            mock_response = Mock()
            mock_response.data = [Mock() for _ in range(150)]
            mock_crud_tool.oms_client.nodes.return_value = mock_response

            mock_crud_tool.get_nodes(node_query)

            # Verify page params were added
            assert hasattr(node_query, "pageParams"), "pageParams should be added to query"
            assert node_query.pageParams.page == 1, f"Expected page=1, got {node_query.pageParams.page}"
            assert node_query.pageParams.pageSize == 200, f"Expected pageSize=200, got {node_query.pageParams.pageSize}"

    def test_pagination_enforcement_disabled(self, mock_crud_tool):
        """Test that pagination is not enforced when disabled."""
        # Mock settings to disable pagination
        with patch("oms_sensemaking.core.oms_crud.SETTINGS") as mock_settings:
            mock_settings.enforce_graphql_pagination = False
            mock_settings.graphql_default_page_size = 200
            mock_settings.graphql_max_page_size = 500

            # Test get_nodes with no page params
            node_query = NodeQuery()
            mock_response = Mock()
            mock_response.data = [Mock() for _ in range(150)]
            mock_crud_tool.oms_client.nodes.return_value = mock_response

            mock_crud_tool.get_nodes(node_query)

            # Verify page params were NOT added
            assert (
                not hasattr(node_query, "pageParams") or node_query.pageParams is None
            ), "pageParams should not be added when enforcement is disabled"

    def test_page_size_clamping(self, mock_crud_tool):
        """Test that page sizes are properly clamped to max values."""
        # Mock settings
        with patch("oms_sensemaking.core.oms_crud.SETTINGS") as mock_settings:
            mock_settings.enforce_graphql_pagination = True
            mock_settings.graphql_default_page_size = 200
            mock_settings.graphql_max_page_size = 500

            mock_response = Mock()
            mock_response.data = []
            mock_crud_tool.oms_client.nodes.return_value = mock_response

            # Test various page sizes
            test_cases = [
                (50, 50),  # Under limit - should remain
                (200, 200),  # At default - should remain
                (500, 500),  # At max - should remain
                (1000, 500),  # Over max - should be clamped
                (None, 200),  # None - should use default
            ]

            for input_size, expected_size in test_cases:
                query = NodeQuery()
                if input_size is not None:
                    query.pageParams = PageParams(page=1, pageSize=input_size)

                mock_crud_tool.get_nodes(query)

                assert (
                    query.pageParams.pageSize == expected_size
                ), f"Expected pageSize={expected_size} for input={input_size}, got {query.pageParams.pageSize}"

    def test_all_crud_methods_pagination(self, mock_crud_tool):
        """Test that all CRUD methods enforce pagination."""
        # Mock settings to enable pagination
        with patch("oms_sensemaking.core.oms_crud.SETTINGS") as mock_settings:
            mock_settings.enforce_graphql_pagination = True
            mock_settings.graphql_default_page_size = 100
            mock_settings.graphql_max_page_size = 300

            # Mock responses
            mock_nodes = Mock()
            mock_nodes.data = [Mock() for _ in range(50)]
            mock_relationships = Mock()
            mock_relationships.data = [Mock() for _ in range(50)]
            mock_attributes = Mock()
            mock_attributes.data = [Mock() for _ in range(50)]
            mock_activities = Mock()
            mock_activities.data = [Mock() for _ in range(50)]
            mock_observations = Mock()
            mock_observations.data = [Mock() for _ in range(50)]

            mock_crud_tool.oms_client.nodes.return_value = mock_nodes
            mock_crud_tool.oms_client.relationships.return_value = mock_relationships
            mock_crud_tool.oms_client.attributes.return_value = mock_attributes
            mock_crud_tool.oms_client.activities.return_value = mock_activities
            mock_crud_tool.oms_client.observations.return_value = mock_observations

            # Test all methods
            methods_to_test = [
                ("get_nodes", NodeQuery()),
                ("get_relationships", RelationshipQuery()),
                ("get_attributes", AttributeQuery()),
                ("get_activities", ActivityQuery()),
                ("get_observations", ObservationQuery()),
            ]

            for method_name, query in methods_to_test:
                method = getattr(mock_crud_tool, method_name)
                method(query)

                # Verify page params were added
                assert hasattr(query, "pageParams"), f"pageParams should be added to {method_name} query"
                assert query.pageParams.page == 1, f"Expected page=1 for {method_name}, got {query.pageParams.page}"
                assert (
                    query.pageParams.pageSize == 100
                ), f"Expected pageSize=100 for {method_name}, got {query.pageParams.pageSize}"


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

    def test_ssl_configuration(self):
        """Test SSL configuration handling."""
        # Test with SSL enabled
        with patch("oms_sensemaking.clients.instances.SETTINGS") as mock_settings:
            mock_settings.db_uri = "postgresql://test:test@localhost:5432/test_db"
            mock_settings.db_ssl = True
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
                    assert connect_args["sslmode"] == "require", "SSL should be required when db_ssl=True"

        # Test with SSL disabled
        with patch("oms_sensemaking.clients.instances.SETTINGS") as mock_settings:
            mock_settings.db_uri = "postgresql://test:test@localhost:5432/test_db"
            mock_settings.db_ssl = False
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
                    assert connect_args["sslmode"] == "prefer", "SSL should be preferred when db_ssl=False"
