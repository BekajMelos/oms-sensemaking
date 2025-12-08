from unittest.mock import MagicMock, Mock

import pytest

from oms_sensemaking.inference.rules.garrison_data_collection import (
    GetGarrisonDataAllAtOnce,
    GetGarrisonDataRetrieverFactory,
    GetGarrisonDataSequential,
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


def test_all_at_once_returns_none_when_no_coords(mock_oms_tool, obs, mocker):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mocker.patch.object(retriever, "_fetch_garrison_coords", return_value=None)

    result = retriever.get_all_garrison_data(obs)
    assert result is None


def test_all_at_once_returns_lat_lon_pairs(mock_oms_tool, obs, mocker):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    # garrison coords are [lon, lat]
    mocker.patch.object(retriever, "_fetch_garrison_coords", return_value=[30.0, 40.0])

    result = retriever.get_all_garrison_data(obs)
    assert result == ([20.0, 10.0], [40.0, 30.0])


def test_fetch_garrison_coords_returns_coords(mock_oms_tool):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)
    mock_result = Mock()
    mock_result.relationships.data = [
        Mock(endNode=Mock(attributes=Mock(data=[Mock(geometry={"coordinates": [30.0, 40.0]})])))
    ]
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = mock_result

    coords = retriever._fetch_garrison_coords("node123")
    assert coords == [30.0, 40.0]


def test_fetch_garrison_coords_handles_attribute_error(mock_oms_tool):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)

    # Simulate missing relationships attribute (AttributeError)
    mock_result = MagicMock()
    mock_result.relationships = None
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = mock_result

    coords = retriever._fetch_garrison_coords("node123")
    assert coords is None


def test_fetch_garrison_coords_handles_index_error(mock_oms_tool):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)

    # Simulate empty relationships data (IndexError)
    mock_result = MagicMock()
    mock_result.relationships.data = []
    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = mock_result

    coords = retriever._fetch_garrison_coords("node123")
    assert coords is None


def test_fetch_garrison_coords_handles_missing_geometry_key(mock_oms_tool):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)

    # Simulate missing 'geometry' key (KeyError)
    attributes_data_mock = [MagicMock()]

    mock_result_missing_geometry = MagicMock()
    mock_result_missing_geometry.relationships.data.attributes.endNode = {"attributes": {"data": attributes_data_mock}}

    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = mock_result_missing_geometry

    coords = retriever._fetch_garrison_coords("node123")
    assert coords is None


def test_fetch_garrison_coords_handles_invalid_geometry_type(mock_oms_tool):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)

    # Simulate 'geometry' not being a dict (TypeError)
    attributes_data_mock = [MagicMock()]

    mock_result_missing_geometry = MagicMock()
    mock_result_missing_geometry.relationships.data.attributes.endNode = {"attributes": {"data": attributes_data_mock}}

    attributes_data_mock[0].geometry = "not_a_dict"

    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = mock_result_missing_geometry

    coords = retriever._fetch_garrison_coords("node123")
    assert coords is None


def test_fetch_garrison_coords_handles_missing_coordinates_key(mock_oms_tool):
    retriever = GetGarrisonDataAllAtOnce(mock_oms_tool)

    # Simulate 'coordinates' missing in geometry dict (KeyError)
    attributes_data_mock = [MagicMock()]

    mock_result_missing_geometry = MagicMock()
    mock_result_missing_geometry.relationships.data.attributes.endNode = {"attributes": {"data": attributes_data_mock}}

    attributes_data_mock[0].geometry = {}

    mock_oms_tool.oms_client.in_out_garrison_with_geo.return_value = mock_result_missing_geometry

    coords = retriever._fetch_garrison_coords("node123")
    assert coords is None


def test_sequential_returns_none_if_no_relationships(mock_oms_tool, obs):
    retriever = GetGarrisonDataSequential(mock_oms_tool)
    mock_oms_tool.get_relationships.return_value.data = []

    result = retriever.get_all_garrison_data(obs)
    assert result is None


def test_sequential_returns_none_if_no_attributes(mock_oms_tool, obs):
    retriever = GetGarrisonDataSequential(mock_oms_tool)

    relationship_mock = Mock(endNodeId="garrison123")
    mock_oms_tool.get_relationships.return_value.data = [relationship_mock]
    mock_oms_tool.get_attributes.return_value.data = []

    result = retriever.get_all_garrison_data(obs)
    assert result is None


def test_sequential_returns_lat_lon_pairs(mock_oms_tool, obs):
    retriever = GetGarrisonDataSequential(mock_oms_tool)

    relationship_mock = Mock(endNodeId="garrison123")
    attribute_mock = Mock(geometry={"coordinates": [30.0, 40.0]})

    mock_oms_tool.get_relationships.return_value.data = [relationship_mock]
    mock_oms_tool.get_attributes.return_value.data = [attribute_mock]

    result = retriever.get_all_garrison_data(obs)
    assert result == ([20.0, 10.0], [40.0, 30.0])


def test_factory_returns_correct_class(mock_oms_tool):
    factory = GetGarrisonDataRetrieverFactory(mock_oms_tool)
    assert isinstance(factory.get_garrison_data_retriever("AllAtOnce"), GetGarrisonDataAllAtOnce)
    assert isinstance(factory.get_garrison_data_retriever("Sequential"), GetGarrisonDataSequential)


def test_factory_invalid_type_raises(mock_oms_tool):
    factory = GetGarrisonDataRetrieverFactory(mock_oms_tool)
    with pytest.raises(ValueError):
        factory.get_garrison_data_retriever("InvalidType")
