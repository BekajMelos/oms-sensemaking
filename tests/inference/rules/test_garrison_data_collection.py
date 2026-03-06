from unittest.mock import Mock

import pytest

from oms_sensemaking.inference.rules.garrison_data_collection import (
    GarrisonData,
    GetGarrisonDataAllAtOnce,
)


@pytest.fixture
def mock_oms_tool():
    return Mock()


@pytest.fixture
def obs():
    return Mock(
        nodeId="node123",
        geometry={"coordinates": [10.0, 20.0]},  # lon, lat
    )


def _make_result(
    *,
    garrison_coords=None,
    activities_data=None,
    include_node=True,
    include_relationships=True,
    include_end_node=True,
    include_attributes=True,
    include_attribute_data=True,
    geometry_value=None,
):
    """
    Build a mock result object that matches the shape accessed by:
      result.node.relationships.data[0].endNode.attributes.data[0].geometry
      result.activities.data
    """
    result = Mock()

    # activities
    if activities_data is None:
        activities_data = []
    result.activities = Mock(data=activities_data)

    # relationships
    result.relationships = Mock()
    result.relationships.data = []

    if not include_relationships:
        return result

    # relationship -> endNode
    rel_item = Mock()
    result.relationships.data.append(rel_item)

    if not include_end_node:
        rel_item.endNode = None
        return result

    end_node = Mock()
    rel_item.endNode = end_node

    # endNode.attributes
    if not include_attributes:
        # No attributes attribute at all
        if hasattr(end_node, "attributes"):
            delattr(end_node, "attributes")
        return result

    attributes = Mock()
    end_node.attributes = attributes

    if not include_attribute_data:
        attributes.data = []
        return result

    # attributes.data[0]
    attr_item = Mock()
    attributes.data = [attr_item]

    # geometry
    if geometry_value is not None:
        attr_item.geometry = geometry_value
    elif garrison_coords is not None:
        attr_item.geometry = {"coordinates": garrison_coords}
    else:
        # missing coordinates
        attr_item.geometry = {}

    return result


def test_all_at_once_returns_none_when_node_missing(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(include_node=False)

    assert retriever.get_all_garrison_data(obs) is None


def test_all_at_once_returns_none_when_relationships_missing(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(include_relationships=False)

    assert retriever.get_all_garrison_data(obs) is None


def test_all_at_once_returns_none_when_attributes_missing(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(include_attributes=False)

    assert retriever.get_all_garrison_data(obs) is None


def test_all_at_once_returns_none_when_attribute_data_empty(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(include_attribute_data=False)

    assert retriever.get_all_garrison_data(obs) is None


def test_all_at_once_returns_none_when_geometry_missing_coordinates(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(garrison_coords=None)

    assert retriever.get_all_garrison_data(obs) is None


def test_all_at_once_returns_none_when_geometry_not_a_dict(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(geometry_value="not_a_dict")

    result = retriever.get_all_garrison_data(obs)
    assert result is None


def test_all_at_once_returns_garrison_data_with_activities(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)

    activities = [Mock(id="a1", name="In Garrison"), Mock(id="a2", name="Out of Garrison")]

    # garrison coords are [lon, lat]
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(
        garrison_coords=[30.0, 40.0],
        activities_data=activities,
    )

    result = retriever.get_all_garrison_data(obs)
    assert isinstance(result, GarrisonData)

    # convert to [lat, lon]
    assert result.object_lat_lon == [20.0, 10.0]

    # convert to [lat, lon]
    assert result.garrison_lat_lon == [40.0, 30.0]

    assert result.activities == activities


def test_all_at_once_calls_custom_query_with_expected_params(mock_oms_tool, obs):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = _make_result(garrison_coords=[30.0, 40.0])

    _ = retriever.get_all_garrison_data(obs)

    # Assert the SDK method is called and includes key args
    mock_oms_tool.oms_client.in_out_garrison_with_geo.assert_called_once()
    kwargs = mock_oms_tool.oms_client.in_out_garrison_with_geo.call_args.kwargs

    assert kwargs["id"] == obs.nodeId
    assert "garrisonIris" in kwargs
    assert "geoIris" in kwargs
    assert "activityName" in kwargs
    assert "activityStates" in kwargs
