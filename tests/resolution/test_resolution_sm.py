import json
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import AttributeAttribute, NodeNode
from oms_sdk.generated.generated_graphql_client.enums import ObjectTier

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.resolution.sensemaker import ResolutionSensemaker


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
def test_attribute(test_node):
    return AttributeAttribute.model_construct(
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node.id,
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
