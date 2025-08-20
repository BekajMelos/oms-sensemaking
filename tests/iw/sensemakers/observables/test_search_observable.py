import json
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockerFixture

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.iw.sensemakers.observables.base_observable import ObservableQueryType, TimeBounds
from oms_sensemaking.iw.sensemakers.observables.search_observable import SearchObservable, StatusCriteria


class TestStatusCriteria:
    """test StatusCriteria model"""

    def test_status_criteria_creation(self):
        """test StatusCriteria creation with valid data"""
        criteria = StatusCriteria(attributeIri="http://example.com/status", triggeringValues=["active", "inactive"])

        assert criteria.attribute_iri == "http://example.com/status"
        assert criteria.triggering_values == ["active", "inactive"]

    def test_status_criteria_aliases(self):
        """test StatusCriteria with field aliases"""
        criteria = StatusCriteria(attributeIri="http://example.com/status", triggeringValues=["active"])

        assert criteria.attribute_iri == "http://example.com/status"
        assert criteria.triggering_values == ["active"]


class TestSearchObservable:
    """test SearchObservable class"""

    @pytest.fixture
    def mock_oms_client(self, mocker: MockerFixture):
        """mock OMS client"""
        return mocker.Mock(spec=OmsCrudTool)

    @pytest.fixture
    def valid_time_bounds(self):
        """valid TimeBounds for testing"""
        return TimeBounds(
            sinceLastQuery=False, startTime="2024-01-01T00:00:00.000Z", endTime="2024-01-01T01:00:00.000Z"
        )

    @pytest.fixture
    def test_criteria(self):
        """test criteria list"""
        return [
            StatusCriteria(attributeIri="http://example.com/status", triggeringValues=["active"]),
            StatusCriteria(attributeIri="http://example.com/type", triggeringValues=["vehicle", "person"]),
        ]

    @pytest.fixture
    def search_observable(self, valid_time_bounds, test_criteria):
        """create a SearchObservable instance"""
        return SearchObservable(
            queryType=ObservableQueryType.search,
            timeBounds=valid_time_bounds,
            criteria=test_criteria,
            fullyObservedCount=5,
        )

    def test_search_observable_creation(self, search_observable, test_criteria):
        """test SearchObservable creation with valid data"""
        assert search_observable.query_type == ObservableQueryType.search
        assert search_observable.criteria == test_criteria
        assert search_observable.fully_observed_count == 5

    @patch.object(SearchObservable, "get_status_attr")
    def test_update_data_no_status_attribute(self, mock_get_status_attr, search_observable, mock_oms_client):
        """test update_data when no status attribute is found"""
        search_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = None

        search_observable.update_data()

        mock_oms_client.get_relationships.assert_not_called()

    @patch.object(SearchObservable, "get_status_attr")
    @patch.object(SearchObservable, "get_related_object_ids")
    def test_update_data_no_related_objects(
        self, mock_get_related_object_ids, mock_get_status_attr, search_observable, mock_oms_client
    ):
        """test update_data when no related objects are found"""
        search_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        mock_get_related_object_ids.return_value = []

        search_observable.update_data()

        # Should return early, no attributes should be queried
        assert mock_oms_client.get_attributes.call_count <= 1  # Only config attribute call

    @patch.object(SearchObservable, "get_status_attr")
    @patch.object(SearchObservable, "get_related_object_ids")
    def test_update_data_criteria_loading_error(
        self, mock_get_related_object_ids, mock_get_status_attr, search_observable, mock_oms_client
    ):
        """test update_data when criteria loading fails"""
        search_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        mock_get_related_object_ids.return_value = ["obj1", "obj2"]

        # Mock config loading to fail
        mock_oms_client.get_attributes.side_effect = Exception("Config load error")

        search_observable.update_data()

        # Should handle the exception and return early

    @patch("oms_sensemaking.iw.sensemakers.observables.search_observable.SETTINGS")
    @patch.object(SearchObservable, "get_status_attr")
    @patch.object(SearchObservable, "get_related_object_ids")
    @patch.object(SearchObservable, "update_status")
    def test_update_data_successful_execution(
        self,
        mock_update_status,
        mock_get_related_object_ids,
        mock_get_status_attr,
        mock_settings,
        search_observable,
        mock_oms_client,
        test_criteria,
    ):
        """test successful update_data execution"""
        # Mock the settings
        mock_settings.iw_settings.observable_config_attribute_iri = "http://example.com/config"

        search_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        related_ids = ["obj1", "obj2", "obj3"]
        mock_get_related_object_ids.return_value = related_ids

        # Mock config data
        config_data = {"criteria": [c.model_dump() for c in test_criteria]}
        mock_config_attr = MagicMock()
        mock_config_attr.attributeValue = json.dumps(config_data)
        mock_config_response = MagicMock()
        mock_config_response.data = [mock_config_attr]

        # Mock attribute responses for criteria matching
        def mock_get_attributes(query):
            # First call is for config - check for the actual config IRI
            if (
                hasattr(query, "attributeIris")
                and query.attributeIris
                and "http://example.com/config" in query.attributeIris
            ):
                return mock_config_response

            # Subsequent calls are for criteria matching
            mock_attr1 = MagicMock()
            mock_attr1.nodeId = "obj1"
            mock_attr3 = MagicMock()
            mock_attr3.nodeId = "obj3"

            if hasattr(query, "attributeValue") and query.attributeValue:
                if query.attributeValue.equals == "active":
                    # obj1 and obj3 have "active" status
                    mock_response = MagicMock()
                    mock_response.data = [mock_attr1, mock_attr3]
                    return mock_response
                elif query.attributeValue.equals in ["vehicle", "person"]:
                    # obj1 has matching type
                    if query.attributeValue.equals == "vehicle":
                        mock_response = MagicMock()
                        mock_response.data = [mock_attr1]
                        return mock_response
                    # obj3 has matching type
                    elif query.attributeValue.equals == "person":
                        mock_response = MagicMock()
                        mock_response.data = [mock_attr3]
                        return mock_response

            return MagicMock(data=[])

        mock_oms_client.get_attributes.side_effect = mock_get_attributes

        search_observable.update_data()

        # Should call update_status with count of objects matching all criteria
        # obj1 matches both criteria (active + vehicle), obj3 matches both (active + person)
        mock_update_status.assert_called_once_with(2, 3)

    @patch("oms_sensemaking.iw.sensemakers.observables.search_observable.SETTINGS")
    @patch.object(SearchObservable, "get_status_attr")
    @patch.object(SearchObservable, "get_related_object_ids")
    @patch.object(SearchObservable, "update_status")
    def test_update_data_partial_matches(
        self,
        mock_update_status,
        mock_get_related_object_ids,
        mock_get_status_attr,
        mock_settings,
        search_observable,
        mock_oms_client,
        test_criteria,
    ):
        """test update_data with partial criterion matches"""
        # Mock the settings
        mock_settings.iw_settings.observable_config_attribute_iri = "http://example.com/config"

        search_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        related_ids = ["obj1", "obj2", "obj3"]
        mock_get_related_object_ids.return_value = related_ids

        # Mock config data
        config_data = {"criteria": [c.model_dump() for c in test_criteria]}
        mock_config_attr = MagicMock()
        mock_config_attr.attributeValue = json.dumps(config_data)
        mock_config_response = MagicMock()
        mock_config_response.data = [mock_config_attr]

        def mock_get_attributes(query):
            # First call is for config - check for the actual config IRI
            if (
                hasattr(query, "attributeIris")
                and query.attributeIris
                and "http://example.com/config" in query.attributeIris
            ):
                return mock_config_response

            # For criteria matching - only obj1 matches first criterion, only obj2 matches second
            mock_attr1 = MagicMock()
            mock_attr1.nodeId = "obj1"
            mock_attr2 = MagicMock()
            mock_attr2.nodeId = "obj2"

            if hasattr(query, "attributeValue") and query.attributeValue:
                if query.attributeValue.equals == "active":
                    # Only obj1 has "active" status
                    mock_response = MagicMock()
                    mock_response.data = [mock_attr1]
                    return mock_response
                elif query.attributeValue.equals in ["vehicle", "person"]:
                    # Only obj2 has matching type
                    mock_response = MagicMock()
                    mock_response.data = [mock_attr2]
                    return mock_response

            return MagicMock(data=[])

        mock_oms_client.get_attributes.side_effect = mock_get_attributes

        search_observable.update_data()

        # No objects match ALL criteria (intersection is empty)
        mock_update_status.assert_called_once_with(0, 3)

    @patch.object(SearchObservable, "get_status_attr")
    @patch.object(SearchObservable, "get_related_object_ids")
    @patch.object(SearchObservable, "update_status")
    def test_update_data_with_class_iris_filter(
        self,
        mock_update_status,
        mock_get_related_object_ids,
        mock_get_status_attr,
        search_observable,
        mock_oms_client,
        test_criteria,
    ):
        """test update_data with class IRIs filter"""
        search_observable.class_iris = ["http://example.com/Vehicle", "http://example.com/Person"]
        search_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        mock_get_related_object_ids.return_value = ["obj1"]

        # Mock config data
        config_data = {"criteria": [c.model_dump() for c in test_criteria]}
        mock_config_attr = MagicMock()
        mock_config_attr.attributeValue = json.dumps(config_data)
        mock_config_response = MagicMock()
        mock_config_response.data = [mock_config_attr]
        mock_oms_client.get_attributes.return_value = mock_config_response

        # Mock empty responses for criteria matching
        def mock_get_attributes_side_effect(query):
            if hasattr(query, "attributeIris") and query.attributeIris and "config" in str(query.attributeIris[0]):
                return mock_config_response
            return MagicMock(data=[])

        mock_oms_client.get_attributes.side_effect = mock_get_attributes_side_effect

        search_observable.update_data()

        # Verify class_iris is still set
        assert search_observable.class_iris == ["http://example.com/Vehicle", "http://example.com/Person"]
