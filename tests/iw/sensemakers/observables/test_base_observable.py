from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeQuery,
    RelationshipRelationship,
    UpdateAttributeInput,
)
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.iw.sensemakers.observables.base_observable import (
    BaseObservable,
    ObservableQueryType,
    TimeBounds,
    format_rfc3339,
)


class TestableBaseObservable(BaseObservable):
    """concrete implementation for testing abstract BaseObservable"""

    def update_data(self):
        """test implementation"""
        pass


class TestTimeBounds:
    """test TimeBounds model validation"""

    def test_time_bounds_with_explicit_times(self):
        """test TimeBounds with explicit start/end times"""
        start_time = "2024-01-01T00:00:00.000Z"
        end_time = "2024-01-01T01:00:00.000Z"

        time_bounds = TimeBounds(sinceLastQuery=False, startTime=start_time, endTime=end_time)

        assert time_bounds.since_last_query is False
        assert time_bounds.start_time == start_time
        assert time_bounds.end_time == end_time

    def test_time_bounds_since_last_query(self):
        """test TimeBounds with sinceLastQuery=True"""
        time_bounds = TimeBounds(sinceLastQuery=True, startTime=None, endTime=None)

        assert time_bounds.since_last_query is True
        assert time_bounds.start_time is not None
        assert time_bounds.end_time is not None
        # should be approximately 15 minutes apart
        start_dt = datetime.fromisoformat(time_bounds.start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(time_bounds.end_time.replace("Z", "+00:00"))
        assert (end_dt - start_dt).total_seconds() == pytest.approx(900, abs=5)  # 15 minutes ±5 seconds

    def test_time_bounds_validation_missing_times(self):
        """test that missing start/end times raise ValueError when sinceLastQuery=False"""
        with pytest.raises(ValueError, match="startTime and endTime are required"):
            TimeBounds(sinceLastQuery=False, startTime=None, endTime=None)

        with pytest.raises(ValueError, match="startTime and endTime are required"):
            TimeBounds(sinceLastQuery=False, startTime="2024-01-01T00:00:00.000Z", endTime=None)


# todo: move this to search_observable test file
# class TestStatusCriteria:
#     """test StatusCriteria model"""
#
#     def test_status_criteria_creation(self):
#         """test StatusCriteria creation with valid data"""
#         criteria = StatusCriteria(attributeIRI="http://example.com/status", triggeringValues=["active", "inactive"])
#
#         assert criteria.attribute_iri == "http://example.com/status"
#         assert criteria.triggering_values == ["active", "inactive"]


class TestBaseObservable:
    """test BaseObservable class"""

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
    def base_observable(self, valid_time_bounds):
        """create a testable BaseObservable instance"""
        return TestableBaseObservable(
            queryType=ObservableQueryType.GEOFENCE, timeBounds=valid_time_bounds, fullyObservedCount=5
        )

    def test_base_observable_creation(self, base_observable, valid_time_bounds):
        """test BaseObservable creation with valid data"""
        assert base_observable.query_type == ObservableQueryType.GEOFENCE
        assert base_observable.time_bounds == valid_time_bounds
        assert base_observable.fully_observed_count == 5

    def test_base_observable_threshold_validation(self, valid_time_bounds):
        """test that at least one threshold is required"""
        with pytest.raises(
            ValueError, match="At least one of fullyObservedCount or fullyObservedPercentage is required"
        ):
            TestableBaseObservable(queryType=ObservableQueryType.GEOFENCE, timeBounds=valid_time_bounds)

    def test_base_observable_percentage_validation(self, valid_time_bounds):
        """test percentage validation"""
        # valid percentage
        observable = TestableBaseObservable(
            queryType=ObservableQueryType.GEOFENCE, timeBounds=valid_time_bounds, fullyObservedPercentage=80
        )
        assert observable.fully_observed_percentage == 80

        # invalid percentage > 100
        with pytest.raises(ValueError):
            TestableBaseObservable(
                queryType=ObservableQueryType.GEOFENCE, timeBounds=valid_time_bounds, fullyObservedPercentage=150
            )

    def test_initialize(self, base_observable, mock_oms_client):
        """test initialize method"""
        observable_id = "test-observable-id"

        result = base_observable.initialize(observable_id, mock_oms_client)

        assert result == base_observable
        assert base_observable.id == observable_id
        assert base_observable.oms_client == mock_oms_client

    def test_ensure_initialized_success(self, base_observable, mock_oms_client):
        """test ensure_initialized with properly initialized observable"""
        base_observable.initialize("test-id", mock_oms_client)

        # should not raise exception
        base_observable.ensure_initialized()

    def test_ensure_initialized_failure(self, base_observable):
        """test ensure_initialized with uninitialized observable"""
        with pytest.raises(ValueError, match="Observable is not properly initialized"):
            base_observable.ensure_initialized()

    def test_get_status_attr_success(self, base_observable, mock_oms_client):
        """test get_status_attr with existing attribute"""
        # setup
        base_observable.initialize("test-id", mock_oms_client)

        mock_attr = MagicMock(spec=AttributeAttribute)
        mock_attr.id = "status-attr-id"
        mock_attr.attributeValue = "not_observed"

        mock_response = MagicMock()
        mock_response.data = [mock_attr]
        mock_oms_client.get_attributes.return_value = mock_response

        # execute
        result = base_observable.get_status_attr()

        # verify
        assert result == mock_attr
        assert base_observable.status_attribute_id == "status-attr-id"
        mock_oms_client.get_attributes.assert_called_once_with(
            AttributeQuery(nodeIds=["test-id"], attributeIris=[SETTINGS.iw_settings.observable_status_attribute_iri])
        )

    def test_get_status_attr_not_found(self, base_observable, mock_oms_client):
        """test get_status_attr with no existing attribute"""
        # setup
        base_observable.initialize("test-id", mock_oms_client)

        mock_response = MagicMock()
        mock_response.data = []
        mock_oms_client.get_attributes.return_value = mock_response

        # execute
        result = base_observable.get_status_attr()

        # verify
        assert result is None
        assert base_observable.status_attribute_id is None

    def test_get_related_object_ids(self, base_observable, mock_oms_client):
        """test get_related_object_ids"""
        # setup
        base_observable.initialize("test-id", mock_oms_client)

        mock_rel1 = MagicMock(spec=RelationshipRelationship)
        mock_rel1.endNodeId = "object-1"
        mock_rel2 = MagicMock(spec=RelationshipRelationship)
        mock_rel2.endNodeId = "object-2"

        mock_response = MagicMock()
        mock_response.data = [mock_rel1, mock_rel2]
        mock_oms_client.get_relationships.return_value = mock_response

        # execute
        result = base_observable.get_related_object_ids()

        # verify
        assert result == ["object-1", "object-2"]
        assert base_observable.related_object_ids == ["object-1", "object-2"]
        mock_oms_client.get_relationships.assert_called_once()

    def test_determine_status_fully_observed_count(self, base_observable):
        """test determine_status with fully observed count threshold"""
        base_observable.fully_observed_count = 5

        result = base_observable.determine_status(6, 10)
        assert result == SETTINGS.iw_settings.observable_statuses["fully_observed"]

    def test_determine_status_fully_observed_percentage(self, base_observable):
        """test determine_status with fully observed percentage threshold"""
        base_observable.fully_observed_count = None
        base_observable.fully_observed_percentage = 0.8

        result = base_observable.determine_status(8, 10)
        assert result == SETTINGS.iw_settings.observable_statuses["fully_observed"]

    def test_determine_status_partially_observed(self, base_observable):
        """test determine_status with partially observed threshold"""
        base_observable.fully_observed_count = 10
        base_observable.partially_observed_count = 3

        result = base_observable.determine_status(5, 10)
        assert result == SETTINGS.iw_settings.observable_statuses["partially_observed"]

    def test_determine_status_not_observed(self, base_observable):
        """test determine_status with not observed result"""
        base_observable.fully_observed_count = 10
        base_observable.partially_observed_count = 5

        result = base_observable.determine_status(2, 10)
        assert result == SETTINGS.iw_settings.observable_statuses["not_observed"]

    @patch.object(TestableBaseObservable, "get_status_attr")
    def test_update_status_no_change(self, mock_get_status_attr, base_observable, mock_oms_client):
        """test update_status method when status doesn't change"""
        # setup
        base_observable.initialize("test-id", mock_oms_client)
        base_observable.status_attribute_id = "status-attr-id"
        base_observable.fully_observed_count = 5

        # mock get_status_attr to return the same status that would be determined
        mock_prev_attr = MagicMock()
        mock_prev_attr.attributeValue = SETTINGS.iw_settings.observable_statuses["fully_observed"]
        mock_get_status_attr.return_value = mock_prev_attr

        # execute with values that would result in "fully_observed" status
        base_observable.update_status(6, 10)

        # verify that update_attribute was NOT called since status didn't change
        mock_oms_client.update_attribute.assert_not_called()

    @patch.object(TestableBaseObservable, "get_status_attr")
    def test_update_status_with_change(self, mock_get_status_attr, base_observable, mock_oms_client):
        """test update_status method when status changes"""
        # setup
        base_observable.initialize("test-id", mock_oms_client)
        base_observable.status_attribute_id = "status-attr-id"
        base_observable.fully_observed_count = 5

        # mock get_status_attr to return different status than what will be determined
        mock_prev_attr = MagicMock()
        mock_prev_attr.attributeValue = "not_observed"
        mock_get_status_attr.return_value = mock_prev_attr

        # execute with values that would result in "fully_observed" status
        base_observable.update_status(6, 10)

        # verify that update_attribute WAS called since status changed
        mock_oms_client.update_attribute.assert_called_once_with(
            UpdateAttributeInput(
                id="status-attr-id",
                attributeValue=SETTINGS.iw_settings.observable_statuses["fully_observed"],
                attributeDisplayValue=SETTINGS.iw_settings.observable_statuses["fully_observed"],
                attributeNormalizedValue=SETTINGS.iw_settings.observable_statuses["fully_observed"],
                isUserEntered=False,
                labels=[SETTINGS.sm_inferenced_label],
            )
        )


def test_format_rfc3339():
    """test format_rfc3339 function"""
    dt = datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=ZoneInfo("UTC"))
    result = format_rfc3339(dt)
    assert result == "2024-01-01T12:30:45.123Z"
