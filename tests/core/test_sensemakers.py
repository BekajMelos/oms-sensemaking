from unittest import mock

import pytest

from oms_sensemaking.core.sensemakers import OmsPublisher, jsonify


def test_jsonify_dict_and_list():
    data = {"a": 1, "b": [2, 3]}
    result = jsonify(data)
    assert result == {"a": 1, "b": [2, 3]}


def test_jsonify_wkbelement(mocker):
    fake_geom = mock.Mock(name="fake_geom")
    fake_geom.wkt = "POINT (1 2)"

    # patch to_shape so that it returns fake_geom
    mocker.patch("oms_sensemaking.core.sensemakers.to_shape", return_value=fake_geom)

    # Pretend fake_wkb is a WKBElement
    from geoalchemy2 import WKBElement

    wkbelement = mocker.Mock(spec=WKBElement)

    result = jsonify(wkbelement)
    assert result == "POINT (1 2)"


def test_jsonify_object_with_to_dict():
    class Obj:
        def to_dict(self):
            return {"x": 42}

    obj = Obj()
    result = jsonify(obj)
    assert result == {"x": 42}


@pytest.mark.parametrize("value", [123, 4.56, True, None])
def test_jsonify_primitives(value):
    assert jsonify(value) == value


def test_jsonify_fallback_to_str():
    class Foo:
        def __str__(self):
            return "foo"

    obj = Foo()
    assert jsonify(obj) == "foo"


class DummyPublisher(OmsPublisher):
    """Test subclass with concrete format_* implementations."""

    def format_nodes(self, data, results):
        # Pretend the data has "nodes" with uuids
        self.node_uuid_list = ["uuid1", "uuid2"]
        return ["node1", "node2"]

    def format_relationships(self, data, results):
        return ["rel1", "rel2"]

    def format_attributes(self, data, results):
        return ["attr1"]


@pytest.fixture
def mock_crud_tool(mocker):
    tool = mocker.Mock()
    # Mock return values for CRUD methods
    tool.create_node.side_effect = [
        mock.Mock(id="db-id-1"),
        mock.Mock(id="db-id-2"),
    ]
    tool.publish_relationships.return_value = ["published-rel"]
    tool.publish_attributes.return_value = ["published-attr"]
    return tool


@pytest.fixture
def publisher(mock_crud_tool):
    return DummyPublisher(mock_crud_tool)


def test_publish_clears_state_and_calls_publishers(publisher, mock_crud_tool):
    # Pre-populate state to ensure publish() resets it
    publisher.node_uuid_list = ["old"]
    publisher.node_id_mapping = {"old": "stale"}

    publisher.publish(data={"foo": "bar"}, results={"baz": "qux"})

    # State should be reset
    assert publisher.node_uuid_list == ["uuid1", "uuid2"]
    assert publisher.node_id_mapping == {"uuid1": "db-id-1", "uuid2": "db-id-2"}

    # Delegations should happen
    assert mock_crud_tool.create_node.call_count == 2
    mock_crud_tool.publish_relationships.assert_called_once_with(["rel1", "rel2"])
    mock_crud_tool.publish_attributes.assert_called_once_with(["attr1"])


def test_publish_nodes_maps_ids(publisher, mock_crud_tool):
    formatted_nodes = ["node1", "node2"]
    publisher.node_uuid_list = ["u1", "u2"]

    published = publisher.publish_nodes(formatted_nodes)

    assert [n.id for n in published] == ["db-id-1", "db-id-2"]
    assert publisher.node_id_mapping == {"u1": "db-id-1", "u2": "db-id-2"}


def test_publish_relationships_delegates(publisher, mock_crud_tool):
    rels = ["rel1"]
    result = publisher.publish_relationships(rels)
    assert result == ["published-rel"]
    mock_crud_tool.publish_relationships.assert_called_once_with(rels)


def test_publish_attributes_delegates(publisher, mock_crud_tool):
    attrs = ["attr1"]
    result = publisher.publish_attributes(attrs)
    assert result == ["published-attr"]
    mock_crud_tool.publish_attributes.assert_called_once_with(attrs)
