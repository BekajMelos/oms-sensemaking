import json
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import AttributeAttribute, NodeNode
from oms_sdk.generated.generated_graphql_client.enums import ObjectTier

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.resolution.sensemaker import DupFinding, ResolutionSensemaker


@pytest.fixture
def test_node():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )


@pytest.fixture
def test_node_a():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_nodeA",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )


@pytest.fixture
def test_node_b():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_nodeB",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )


@pytest.fixture
def test_attribute(test_node):
    return AttributeAttribute.model_construct(
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_a(test_node_a):
    return AttributeAttribute.model_construct(
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node_a.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_b(test_node_b):
    return AttributeAttribute.model_construct(
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node_b.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def duplicate_object_iris():
    with open(SETTINGS.duplicate_object_iris_file_path) as f:
        dup_iris = json.load(f)
        return dup_iris


@pytest.fixture
def mock_crud_tool(test_node):
    mock_tool = mock.MagicMock(spec=OmsCrudTool)
    mock_tool.get_node.return_value = test_node
    return mock_tool


@pytest.fixture
def sensemaker(duplicate_object_iris, mock_crud_tool):
    return ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)


def test_current_class_iri(sensemaker, test_attribute, test_node):
    result = sensemaker.current_class_iri(test_attribute)
    assert result == test_node.classIri


@pytest.mark.parametrize(
    "attr_kwargs",
    [
        {
            "attributeIri": "https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
            "attributeValue": "ABCD1234",
            "nodeId": None,
        },
        {"attributeIri": "fake_attr_iri", "attributeValue": "ABCD1234", "nodeId": uuid4()},
        {
            "attributeIri": "https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
            "attributeValue": "",
            "nodeId": uuid4,
        },
    ],
)
def test_is_valid_false_cases(duplicate_object_iris, attr_kwargs):
    attr = AttributeAttribute.model_construct(**attr_kwargs, sourceId=uuid4(), acm=DEFAULT_ACM)
    mock_crud = mock.MagicMock(spec=OmsCrudTool)
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud)
    result = sensemaker.is_valid(attr)
    assert result == (False, None)


def test_is_valid_already_ran_false(duplicate_object_iris, test_attribute, mock_crud_tool):
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    with mock.patch.object(ResolutionSensemaker, "has_already_ran", return_value=True):
        assert sensemaker.is_valid(test_attribute) == (False, None)


def test_is_valid_true_case(duplicate_object_iris, test_attribute, mock_crud_tool):
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    with mock.patch.object(ResolutionSensemaker, "has_already_ran", return_value=False):
        valid, class_iri = sensemaker.is_valid(test_attribute)
        assert valid is True
        assert class_iri == "https://foundry.ai.mil/ontology/4901-001/Facility"


def test_create_duplicate_findings_creates_dups_and_relationships(
    duplicate_object_iris, mock_crud_tool, test_node, test_node_a, test_node_b, test_attribute
):
    # Setup
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    # Call method
    dups = sensemaker.create_duplicate_findings(test_attribute, [test_node, test_node_a, test_node_b])

    # Assertions
    assert len(dups) == 2
    assert all(isinstance(d, DupFinding) for d in dups)
    assert dups[0].end_node_id == test_node_a.id
    assert dups[1].end_node_id == test_node_b.id

    # Check if relationships were created
    assert mock_crud_tool.create_relationship.call_count == 2


def test_has_already_ran_true(duplicate_object_iris, mock_crud_tool):
    mock_crud_tool.get_relationships.return_value.data = [1]  # dummy data

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    assert sensemaker.has_already_ran(uuid4()) is True


def test_has_already_ran_false(duplicate_object_iris, mock_crud_tool):
    mock_crud_tool.get_relationships.return_value.data = []

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    assert sensemaker.has_already_ran(uuid4()) is False


def test_find_duplicates_returns_first_nonempty_group(
    duplicate_object_iris, mock_crud_tool, test_node, test_node_a, test_node_b, test_attribute_a, test_attribute_b
):
    # Return empty for first group, non-empty for second
    mock_crud_tool.get_nodes.side_effect = [mock.MagicMock(data=[]), mock.MagicMock(data=[test_node_a, test_node_b])]

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    duplicates = sensemaker.find_duplicates([[test_attribute_a], [test_attribute_b]])

    assert duplicates == [test_node_a, test_node_b]
