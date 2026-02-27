from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeQuery,
    NodeNode,
    RelationshipNodeQuery,
    RelationshipQuery,
    RelationshipRelationship,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from pytest_mock import MockerFixture

from oms_sensemaking.core.oms_crud import OmsCrudTool
from src.oms_sensemaking.object_standards.sensemaker import (
    ObjectStandardsDataRetriever,
)


@pytest.fixture
def person_obj(mocker: MockerFixture):
    node = mocker.Mock(spec=NodeNode)
    node.id = "person_id"
    node.name = "Person node"
    node.tier = "DERIVATIVE"
    node.classIri = "valid_iri"

    return node


# Mocked nodes
@pytest.fixture
def person_name_attr(mocker: MockerFixture):
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "incAttr1"
    attr.attributeIri = "valid_attribute_iri"
    attr.attributeValue = "Name of person"
    attr.sourceId = "source_id"
    attr.valueStart = "2024-01-01T00:00:00+00:00"
    attr.valueEnd = "2024-05-01T00:00:00+00:00"
    attr.labels = []
    return attr


@pytest.fixture
def person_to_base_rel(mocker: MockerFixture):
    relationship = mocker.Mock(spec=RelationshipRelationship)
    relationship.id = "relationship_id"
    relationship.objectPropertyIri = "valid_relationship_iri"
    relationship.sourceId = "source_id"
    relationship.startNodeId = "person_id"
    relationship.endNodeId = "random_base_id"

    return relationship


@pytest.fixture
def mock_oms_client():
    return MagicMock(spec=Client)


@pytest.fixture
def mock_crud_tool(mock_oms_client):
    crud_tool = MagicMock(spec=OmsCrudTool)
    crud_tool.oms_client = mock_oms_client
    return crud_tool


def test_data_retriever_no_data(mock_crud_tool, person_obj):
    data_retriever = ObjectStandardsDataRetriever()
    result = data_retriever.retrieve_data_for_grading(mock_crud_tool, person_obj, [], [])
    assert result["attributes"] is None
    assert result["relationships"] is None


def test_data_retriever_attr_only(mock_crud_tool, person_obj, person_name_attr):
    data_retriever = ObjectStandardsDataRetriever()
    test_attr_iri_list = ["some_iri"]
    mock_crud_tool.get_attributes.return_value = SimpleNamespace(data=[person_name_attr])

    result = data_retriever.retrieve_data_for_grading(mock_crud_tool, person_obj, test_attr_iri_list, [])
    mock_crud_tool.get_attributes.assert_called_with(
        AttributeQuery(nodeIds=[person_obj.id], attributeIris=test_attr_iri_list)
    )
    assert result["attributes"] == [person_name_attr]
    assert result["relationships"] is None


def test_data_retriever_rel_only(mock_crud_tool, person_obj, person_to_base_rel):
    data_retriever = ObjectStandardsDataRetriever()
    test_rel_iri_list = ["some_iri"]
    mock_crud_tool.get_relationships.return_value = SimpleNamespace(data=[person_to_base_rel])

    result = data_retriever.retrieve_data_for_grading(mock_crud_tool, person_obj, [], test_rel_iri_list)
    mock_crud_tool.get_relationships.assert_called_with(
        RelationshipQuery(nodes=RelationshipNodeQuery(nodeIds=[person_obj.id]), objectPropertyIris=test_rel_iri_list)
    )
    assert result["attributes"] is None
    assert result["relationships"] == [person_to_base_rel]


def test_data_retriever_attr_rel(mock_crud_tool, person_obj, person_name_attr, person_to_base_rel):
    data_retriever = ObjectStandardsDataRetriever()
    test_attr_iri_list = ["some_iri"]
    test_rel_iri_list = ["some_iri"]
    mock_crud_tool.get_attributes.return_value = SimpleNamespace(data=[person_name_attr])
    mock_crud_tool.get_relationships.return_value = SimpleNamespace(data=[person_to_base_rel])

    result = data_retriever.retrieve_data_for_grading(mock_crud_tool, person_obj, test_attr_iri_list, test_rel_iri_list)
    mock_crud_tool.get_attributes.assert_called_with(
        AttributeQuery(nodeIds=[person_obj.id], attributeIris=test_attr_iri_list)
    )
    mock_crud_tool.get_relationships.assert_called_with(
        RelationshipQuery(nodes=RelationshipNodeQuery(nodeIds=[person_obj.id]), objectPropertyIris=test_rel_iri_list)
    )
    assert result["attributes"] == [person_name_attr]
    assert result["relationships"] == [person_to_base_rel]
