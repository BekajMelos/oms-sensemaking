from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.core.oms_crud import OmsCrudTool
from src.oms_sensemaking.object_minimums.sensemaker import (
    ObjectMinimumDataRetriever,
    ObjectMinimums,
)


@pytest.fixture
def sensemaker():
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_retriever = MagicMock(spec=ObjectMinimumDataRetriever)
    mock_rubric = MagicMock()
    rubric_criteria = {}

    return ObjectMinimums(
        oms_crud_tool=mock_oms_crud_tool,
        obj_min_retriever=mock_retriever,
        obj_min_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )


def test_process_data_no_required_iris(sensemaker):
    attribute_of_node = MagicMock(spec=AttributeAttribute)
    attribute_of_node.nodeId = str(uuid4())

    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    sensemaker.oms_crud_tool.get_node.return_value = mock_node

    sensemaker._get_required_iris = MagicMock(return_value=([], []))

    result = sensemaker.process_data(attribute_of_node)

    assert not sensemaker.obj_min_retriever.retrieve_data_for_grading.called
    assert result == []


def test_process_data_with_attributes_and_relationships(sensemaker):
    attribute_of_node = MagicMock(spec=AttributeAttribute)
    attribute_of_node.nodeId = str(uuid4())

    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    sensemaker.oms_crud_tool.get_node.return_value = mock_node

    required_attributes = ["iri1", "iri2"]
    required_relationships = ["relIri1", "relIri2"]

    sensemaker._get_required_iris = MagicMock(return_value=(required_attributes, required_relationships))

    mock_attributes = [{"attribute": "value"}]
    mock_relationships = [{"relationship": "value"}]

    sensemaker.obj_min_retriever.retrieve_data_for_grading.return_value = {
        "attributes": mock_attributes,
        "relationships": mock_relationships,
    }

    mock_grade = MagicMock()
    sensemaker._calculate_grade = MagicMock(return_value=mock_grade)

    result = sensemaker.process_data(attribute_of_node)

    sensemaker.obj_min_retriever.retrieve_data_for_grading.assert_called_once_with(
        sensemaker.oms_crud_tool, mock_node, required_attributes, required_relationships
    )
    assert result == []


@patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_node")
def test_get_required_iris(mock_get_node):
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_retriever = MagicMock(spec=ObjectMinimumDataRetriever)
    mock_rubric = MagicMock()
    class_iri = "http://example.org/ClassIRI"
    rubric_criteria = {class_iri: {"ATTRIBUTES": ["iri1", "iri2"], "RELATIONSHIPS": ["relIri1"]}}

    sensemaker = ObjectMinimums(
        oms_crud_tool=mock_oms_crud_tool,
        obj_min_retriever=mock_retriever,
        obj_min_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    required_attributes, required_relationships = sensemaker._get_required_iris(class_iri)

    assert required_attributes == ["iri1", "iri2"]
    assert required_relationships == ["relIri1"]


@patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_node")
def test_calculate_grade(mock_get_node, sensemaker):
    attributes = [{"attribute": "value"}]
    relationships = [{"relationship": "value"}]

    mock_rubric = MagicMock()
    sensemaker.obj_min_rubric = mock_rubric

    sensemaker._calculate_grade(attributes, relationships)

    mock_rubric.grade.assert_called_once_with(attributes=attributes, relationships=relationships)
