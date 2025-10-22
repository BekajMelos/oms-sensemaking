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
