from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    NodeNode,
    NodesNodes,
    ObjectTier,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.get_attributes import (
    GetAllAttributesAtOnce,
    GetMilSymbolAttributeFactory,
    SequentialGetAllAttributes,
)


@pytest.fixture
def mock_oms_crud_tool():
    return mock.MagicMock(spec=OmsCrudTool)


@pytest.fixture
def mock_oms_node() -> NodeNode:
    node = NodeNode.model_construct(
        id=uuid4(),
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
        name="test",
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
        symbolIdCode=None,
        labels=[],
    )

    return node


@pytest.fixture
def mock_attribute() -> AttributeAttribute:
    attribute_val = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeValue="true",
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    return attribute_val


def test_get_affiliation_of_parent_nodes_no_parents(mock_oms_crud_tool, mock_oms_node):
    retriever = GetAllAttributesAtOnce(mock_oms_crud_tool)
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[])
    result = retriever.get_affiliation_of_parent_nodes(mock_oms_node)
    assert result is None
    mock_oms_crud_tool.get_nodes.assert_called_once()


def test_get_affiliation_of_parent_nodes_with_affiliation(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = GetAllAttributesAtOnce(mock_oms_crud_tool)
    parent_node = mock.MagicMock()
    parent_node.id = "parent-1"
    parent_node.attributeValue = "hostile"
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[parent_node])
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [mock_attribute]

    result = retriever.get_affiliation_of_parent_nodes(mock_oms_node)
    assert result == mock_attribute
    mock_oms_crud_tool.get_node_attribute_by_iri.assert_called_once_with(
        "parent-1", SETTINGS.mil_symbol_settings.affiliation_iris
    )


def test_get_all_mil_sym_attrs_for_enrichment_happy_path(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = GetAllAttributesAtOnce(mock_oms_crud_tool)

    all_attributes = mock.MagicMock()
    all_attributes.context.data = [mock_attribute]
    all_attributes.affiliation.data = [mock_attribute]
    all_attributes.status.data = [mock_attribute]
    all_attributes.echelon.data = [mock_attribute]

    mock_oms_crud_tool.get_mil_symbol_attr.return_value = all_attributes

    result = retriever.get_all_mil_sym_attrs_for_enrichment(mock_oms_node)
    assert result == [mock_attribute, mock_attribute, mock_attribute, mock_attribute]


def test_get_all_mil_sym_attrs_for_enrichment_fallback_affiliation(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = GetAllAttributesAtOnce(mock_oms_crud_tool)
    mock_oms_node.tier = ObjectTier.DERIVATIVE

    all_attributes = mock.MagicMock()
    all_attributes.context.data = []
    all_attributes.affiliation.data = []
    all_attributes.status.data = []
    all_attributes.echelon.data = []

    mock_oms_crud_tool.get_mil_symbol_attr.return_value = all_attributes
    retriever.get_affiliation_of_parent_nodes = mock.MagicMock(return_value=mock_attribute)

    result = retriever.get_all_mil_sym_attrs_for_enrichment(mock_oms_node)
    # Only affiliation found from parent
    assert result[1] == mock_attribute


def test_sequential_get_context_true(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = SequentialGetAllAttributes(mock_oms_crud_tool)
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [mock_attribute]

    result = retriever.get_context(mock_oms_node)
    assert result == mock_attribute


def test_sequential_get_context_none(mock_oms_crud_tool, mock_oms_node):
    retriever = SequentialGetAllAttributes(mock_oms_crud_tool)
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = []
    result = retriever.get_context(mock_oms_node)
    assert result is None


def test_sequential_get_affiliation_direct(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = SequentialGetAllAttributes(mock_oms_crud_tool)
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [mock_attribute]

    result = retriever.get_affiliation(mock_oms_node)
    assert result == mock_attribute


def test_sequential_get_affiliation_from_parent(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = SequentialGetAllAttributes(mock_oms_crud_tool)
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = []
    mock_oms_node.tier = ObjectTier.DERIVATIVE
    retriever.get_affiliation_of_parent_nodes = mock.MagicMock(return_value=mock_attribute)

    result = retriever.get_affiliation(mock_oms_node)
    assert result == mock_attribute


def test_sequential_get_status(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = SequentialGetAllAttributes(mock_oms_crud_tool)
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [mock_attribute]
    result = retriever.get_status(mock_oms_node)
    assert result == mock_attribute


def test_sequential_get_echelon_none(mock_oms_crud_tool, mock_oms_node):
    retriever = SequentialGetAllAttributes(mock_oms_crud_tool)
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = []
    result = retriever.get_echelon(mock_oms_node)
    assert result is None


def test_sequential_get_all_mil_sym_attrs_for_enrichment(mock_oms_crud_tool, mock_oms_node, mock_attribute):
    retriever = SequentialGetAllAttributes(mock_oms_crud_tool)
    retriever.get_context = mock.MagicMock(return_value=mock_attribute)
    retriever.get_affiliation = mock.MagicMock(return_value=mock_attribute)
    retriever.get_status = mock.MagicMock(return_value=mock_attribute)
    retriever.get_echelon = mock.MagicMock(return_value=mock_attribute)

    result = retriever.get_all_mil_sym_attrs_for_enrichment(mock_oms_node)
    assert result == [mock_attribute, mock_attribute, mock_attribute, mock_attribute]


def test_factory_returns_correct_types(mock_oms_crud_tool):
    factory = GetMilSymbolAttributeFactory(mock_oms_crud_tool)

    seq = factory.get_attribute_retriever("Sequential")
    all_at_once = factory.get_attribute_retriever("AllAtOnce")

    assert isinstance(seq, SequentialGetAllAttributes)
    assert isinstance(all_at_once, GetAllAttributesAtOnce)


def test_factory_invalid_type(mock_oms_crud_tool):
    factory = GetMilSymbolAttributeFactory(mock_oms_crud_tool)
    with pytest.raises(ValueError):
        factory.get_attribute_retriever("InvalidType")
