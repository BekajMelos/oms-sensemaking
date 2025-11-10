from oms_sdk.generated.generated_graphql_client import Client
from pytest_mock import MockerFixture

from oms_sensemaking.core.oms_crud import OmsCrudTool


class OmsCrudToolHelper(OmsCrudTool):
    def __init__(self):
        self.oms_client = None


def test_publish_nodes(mocker: MockerFixture):
    client = mocker.Mock(spec=Client)
    spy = mocker.spy(client, "create_node")

    nodes = []
    for node in range(5):
        nodes.append(node)

    helper = OmsCrudToolHelper()
    helper.oms_client = client
    helper.publish_nodes(nodes)
    assert spy.call_count == len(nodes)


def test_publish_relationships(mocker: MockerFixture):
    client = mocker.Mock(spec=Client)
    spy = mocker.spy(client, "create_relationship")

    relationships = []
    for relationship in range(5):
        relationships.append(relationship)

    helper = OmsCrudToolHelper()
    helper.oms_client = client
    helper.publish_relationships(relationships)
    assert spy.call_count == len(relationships)


def test_publish_attributes(mocker: MockerFixture):
    client = mocker.Mock(spec=Client)
    spy = mocker.spy(client, "create_attribute")

    attributes = []
    for attribute in range(5):
        attributes.append(attribute)

    helper = OmsCrudToolHelper()
    helper.oms_client = client
    helper.publish_attributes(attributes)
    assert spy.call_count == len(attributes)


def test_get_node_attribute_by_iri_no_results(mocker: MockerFixture):
    tool = OmsCrudToolHelper()
    tool.get_attributes = mocker.Mock(return_value=mocker.Mock(data=[]))

    res = tool.get_node_attribute_by_iri("id", ["iri"])
    assert res == []


def test_get_node_attribute_by_iri_with_results(mocker: MockerFixture):
    fake_attr = object()
    tool = OmsCrudToolHelper()
    tool.get_attributes = mocker.Mock(return_value=mocker.Mock(data=[fake_attr]))

    res = tool.get_node_attribute_by_iri("id", ["iri"])
    assert res == [fake_attr]


def test_delete_nodes_by_tags_loops_until_empty(mocker: MockerFixture):
    tool = OmsCrudToolHelper()

    resp1 = mocker.Mock(data=[mocker.Mock(id="a"), mocker.Mock(id="b")])
    resp2 = mocker.Mock(data=[])

    tool.oms_client = mocker.Mock(nodes=mocker.Mock(side_effect=[resp1, resp2]))
    tool.delete_node = mocker.Mock()

    tool.delete_nodes_by_tags(["x"])

    assert tool.oms_client.nodes.call_count == 2
    assert tool.delete_node.call_count == 2
    tool.delete_node.assert_any_call("a")
    tool.delete_node.assert_any_call("b")


def test_delete_activities_by_tags_loops_until_empty(mocker: MockerFixture):
    tool = OmsCrudToolHelper()

    resp1 = mocker.Mock(data=[mocker.Mock(id="a1"), mocker.Mock(id="a2")])
    resp2 = mocker.Mock(data=[])

    tool.oms_client = mocker.Mock(activities=mocker.Mock(side_effect=[resp1, resp2]))
    tool.delete_activity = mocker.Mock()

    tool.delete_activities_by_tags(["tagA"])

    assert tool.oms_client.activities.call_count == 2
    assert tool.delete_activity.call_count == 2
    tool.delete_activity.assert_any_call("a1")
    tool.delete_activity.assert_any_call("a2")
