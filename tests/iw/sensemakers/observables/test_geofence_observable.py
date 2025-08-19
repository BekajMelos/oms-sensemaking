import json
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockerFixture

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.iw.sensemakers.observables.base_observable import ObservableQueryType, TimeBounds
from oms_sensemaking.iw.sensemakers.observables.geofence_observable import GeofenceObservable, GeoJSONPolygon


class TestGeoJSONPolygon:
    """test GeoJSONPolygon model"""

    def test_geojson_polygon_creation(self):
        """test GeoJSONPolygon creation with valid coordinates"""
        coordinates = [[[-100.0, 40.0], [-101.0, 40.0], [-101.0, 41.0], [-100.0, 41.0], [-100.0, 40.0]]]
        polygon = GeoJSONPolygon(coordinates=coordinates)

        assert polygon.type == "Polygon"
        assert polygon.coordinates == coordinates


class TestGeofenceObservable:
    """test GeofenceObservable class"""

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
    def test_polygon(self):
        """test GeoJSON polygon"""
        return GeoJSONPolygon(
            coordinates=[[[-100.0, 40.0], [-101.0, 40.0], [-101.0, 41.0], [-100.0, 41.0], [-100.0, 40.0]]]
        )

    @pytest.fixture
    def geofence_observable(self, valid_time_bounds, test_polygon):
        """create a GeofenceObservable instance"""
        return GeofenceObservable(
            queryType=ObservableQueryType.GEOFENCE,
            timeBounds=valid_time_bounds,
            location=test_polygon,
            fullyObservedCount=5,
        )

    def test_geofence_observable_creation(self, geofence_observable, test_polygon):
        """test GeofenceObservable creation with valid data"""
        assert geofence_observable.query_type == ObservableQueryType.GEOFENCE
        assert geofence_observable.location == test_polygon
        assert geofence_observable.fully_observed_count == 5

    @patch.object(GeofenceObservable, "get_status_attr")
    def test_update_data_no_status_attribute(self, mock_get_status_attr, geofence_observable, mock_oms_client):
        geofence_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = None
        geofence_observable.update_data()
        mock_oms_client.get_relationships.assert_not_called()

    @patch.object(GeofenceObservable, "get_status_attr")
    @patch.object(GeofenceObservable, "get_related_object_ids")
    def test_update_data_no_related_objects(
        self, mock_get_related_object_ids, mock_get_status_attr, geofence_observable, mock_oms_client
    ):
        geofence_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        mock_get_related_object_ids.return_value = []
        geofence_observable.update_data()
        mock_oms_client.get_observations.assert_not_called()

    @patch.object(GeofenceObservable, "get_status_attr")
    @patch.object(GeofenceObservable, "get_related_object_ids")
    def test_update_data_geometry_loading_error(
        self, mock_get_related_object_ids, mock_get_status_attr, geofence_observable, mock_oms_client
    ):
        geofence_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        mock_get_related_object_ids.return_value = ["obj1", "obj2"]
        mock_oms_client.get_attributes.side_effect = Exception("Config load error")
        geofence_observable.update_data()
        mock_oms_client.get_observations.assert_not_called()

    @patch.object(GeofenceObservable, "get_status_attr")
    @patch.object(GeofenceObservable, "get_related_object_ids")
    @patch.object(GeofenceObservable, "update_status")
    def test_update_data_successful_execution(
        self,
        mock_update_status,
        mock_get_related_object_ids,
        mock_get_status_attr,
        geofence_observable,
        mock_oms_client,
        test_polygon,
    ):
        geofence_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        related_ids = ["obj1", "obj2", "obj3"]
        mock_get_related_object_ids.return_value = related_ids
        config_data = {"location": test_polygon.model_dump()}
        mock_config_attr = MagicMock()
        mock_config_attr.attributeValue = json.dumps(config_data)
        mock_config_response = MagicMock()
        mock_config_response.data = [mock_config_attr]
        mock_oms_client.get_attributes.return_value = mock_config_response
        mock_obs1 = MagicMock()
        mock_obs1.nodeId = "obj1"
        mock_obs3 = MagicMock()
        mock_obs3.nodeId = "obj3"

        def mock_get_observations(query):
            # use attribute access instead of subscript
            if hasattr(query.nodeIds, "in_") and query.nodeIds.in_ == ["obj1"]:
                mock_response = MagicMock()
                mock_response.data = [mock_obs1]
                return mock_response
            elif hasattr(query.nodeIds, "in_") and query.nodeIds.in_ == ["obj2"]:
                mock_response = MagicMock()
                mock_response.data = []
                return mock_response
            elif hasattr(query.nodeIds, "in_") and query.nodeIds.in_ == ["obj3"]:
                mock_response = MagicMock()
                mock_response.data = [mock_obs3]
                return mock_response
            return MagicMock(data=[])

        mock_oms_client.get_observations.side_effect = mock_get_observations
        geofence_observable.update_data()
        assert mock_oms_client.get_attributes.call_count == 1
        assert mock_oms_client.get_observations.call_count == 3
        mock_update_status.assert_called_once_with(2, 3)

    @patch.object(GeofenceObservable, "get_status_attr")
    @patch.object(GeofenceObservable, "get_related_object_ids")
    @patch.object(GeofenceObservable, "update_status")
    def test_update_data_with_class_iris_filter(
        self,
        mock_update_status,
        mock_get_related_object_ids,
        mock_get_status_attr,
        geofence_observable,
        mock_oms_client,
        test_polygon,
    ):
        geofence_observable.class_iris = ["http://example.com/Vehicle", "http://example.com/Person"]
        geofence_observable.initialize("test-id", mock_oms_client)
        mock_get_status_attr.return_value = MagicMock()
        mock_get_related_object_ids.return_value = ["obj1"]
        config_data = {"location": test_polygon.model_dump()}
        mock_config_attr = MagicMock()
        mock_config_attr.attributeValue = json.dumps(config_data)
        mock_config_response = MagicMock()
        mock_config_response.data = [mock_config_attr]
        mock_oms_client.get_attributes.return_value = mock_config_response
        mock_obs_response = MagicMock()
        mock_obs_response.data = []
        mock_oms_client.get_observations.return_value = mock_obs_response
        geofence_observable.update_data()
        assert geofence_observable.class_iris == ["http://example.com/Vehicle", "http://example.com/Person"]
