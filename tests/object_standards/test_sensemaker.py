from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    NodesNodes,
    RelationshipRelationship,
)

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.object_standards.object_standards_models import RequiredIris
from src.oms_sensemaking.object_standards.sensemaker import (
    ObjectStandards,
    ObjectStandardsDataRetriever,
)


@pytest.fixture
def sensemaker():
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_ontology_service = MagicMock()
    mock_retriever = MagicMock(spec=ObjectStandardsDataRetriever)
    mock_rubric = MagicMock()
    rubric_criteria = {}

    return ObjectStandards(
        oms_crud_tool=mock_oms_crud_tool,
        ontology_service=mock_ontology_service,
        obj_standards_retriever=mock_retriever,
        obj_standards_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )


def test_process_data_no_required_iris(sensemaker):
    attribute_of_node = MagicMock(spec=AttributeAttribute)
    attribute_of_node.nodeId = str(uuid4())

    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    sensemaker.oms_crud_tool.get_node.return_value = mock_node

    sensemaker._get_required_iris = MagicMock(return_value=RequiredIris())

    result = sensemaker.process_data(attribute_of_node)

    assert not sensemaker.obj_standards_retriever.retrieve_data_for_grading.called
    assert result == []


def test_process_data_with_attributes_and_relationships(sensemaker):
    attribute_of_node = MagicMock(spec=AttributeAttribute)
    attribute_of_node.nodeId = str(uuid4())

    mock_nodes = MagicMock(spec=NodesNodes)
    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    mock_nodes.data = [mock_node]
    sensemaker.oms_crud_tool.get_nodes.return_value = mock_nodes

    required_attributes = ["iri1", "iri2"]
    required_relationships = ["relIri1", "relIri2"]

    sensemaker._get_required_iris = MagicMock(
        return_value=RequiredIris(attribute_iris=required_attributes, relationship_iris=required_relationships)
    )

    mock_attributes = [{"attribute": "value"}]
    mock_relationships = [{"relationship": "value"}]

    sensemaker.obj_standards_retriever.retrieve_data_for_grading.return_value = {
        "attributes": mock_attributes,
        "relationships": mock_relationships,
    }

    mock_grade = MagicMock()
    sensemaker._calculate_grade = MagicMock(return_value=mock_grade)

    result = sensemaker.process_data(attribute_of_node)

    sensemaker.obj_standards_retriever.retrieve_data_for_grading.assert_called_once_with(
        sensemaker.oms_crud_tool, mock_node, required_attributes, required_relationships
    )
    assert result == []


@patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_node")
def test_get_required_iris(mock_get_node):
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_ontology_service = MagicMock()
    mock_retriever = MagicMock(spec=ObjectStandardsDataRetriever)
    mock_rubric = MagicMock()
    class_iri = "http://example.org/ClassIRI"
    rubric_criteria = {class_iri: {"ATTRIBUTES": ["iri1", "iri2"], "RELATIONSHIPS": ["relIri1"]}}

    mock_node = MagicMock()
    mock_node.classIri = class_iri

    sensemaker = ObjectStandards(
        oms_crud_tool=mock_oms_crud_tool,
        ontology_service=mock_ontology_service,
        obj_standards_retriever=mock_retriever,
        obj_standards_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    required_iris = sensemaker._get_required_iris(mock_node)

    assert required_iris.attribute_iris == ["iri1", "iri2"]
    assert required_iris.relationship_iris == ["relIri1"]


@patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_node")
def test_calculate_grade(mock_get_node, sensemaker):
    attributes = [{"attribute": "value"}]
    relationships = [{"relationship": "value"}]

    mock_rubric = MagicMock()
    sensemaker.obj_standards_rubric = mock_rubric

    sensemaker._calculate_grade(attributes, relationships)

    mock_rubric.grade.assert_called_once_with(attributes=attributes, relationships=relationships)


def test_process_data_attribute_passed_in(sensemaker):
    attribute_of_node = MagicMock(spec=AttributeAttribute)
    attribute_of_node.nodeId = str(uuid4())

    mock_nodes = MagicMock(spec=NodesNodes)
    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    mock_nodes.data = [mock_node]
    sensemaker.oms_crud_tool.get_nodes.return_value = mock_nodes

    required_attributes = ["iri1", "iri2"]
    required_relationships = ["relIri1", "relIri2"]

    sensemaker._get_required_iris = MagicMock(
        return_value=RequiredIris(attribute_iris=required_attributes, relationship_iris=required_relationships)
    )

    mock_attributes = [{"attribute": "value"}]
    mock_relationships = [{"relationship": "value"}]

    sensemaker.obj_standards_retriever.retrieve_data_for_grading.return_value = {
        "attributes": mock_attributes,
        "relationships": mock_relationships,
    }

    mock_grade = MagicMock()
    sensemaker._calculate_grade = MagicMock(return_value=mock_grade)

    result = sensemaker.process_data(attribute_of_node)

    sensemaker.obj_standards_retriever.retrieve_data_for_grading.assert_called_once_with(
        sensemaker.oms_crud_tool, mock_node, required_attributes, required_relationships
    )

    sensemaker._calculate_grade.assert_called_once_with(mock_attributes, mock_relationships)
    assert result == []


def test_process_data_rel_passed_in(sensemaker):
    rel_of_node = MagicMock(spec=RelationshipRelationship)
    rel_of_node.startNodeId = str(uuid4())
    rel_of_node.endNodeId = str(uuid4())

    mock_nodes = MagicMock(spec=NodesNodes)
    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    mock_node2 = MagicMock()
    mock_node2.classIri = "http://example.org/ClassIRI"
    mock_nodes.data = [mock_node, mock_node2]
    sensemaker.oms_crud_tool.get_nodes.return_value = mock_nodes

    required_attributes = ["iri1", "iri2"]
    required_relationships = ["relIri1", "relIri2"]

    sensemaker._get_required_iris = MagicMock(
        return_value=RequiredIris(attribute_iris=required_attributes, relationship_iris=required_relationships)
    )

    mock_attributes = [{"attribute": "value"}]
    mock_relationships = [{"relationship": "value"}]

    sensemaker.obj_standards_retriever.retrieve_data_for_grading.return_value = {
        "attributes": mock_attributes,
        "relationships": mock_relationships,
    }

    mock_grade = MagicMock()
    sensemaker._calculate_grade = MagicMock(return_value=mock_grade)

    result = sensemaker.process_data(rel_of_node)

    assert sensemaker.obj_standards_retriever.retrieve_data_for_grading.call_count == 2
    assert sensemaker._get_required_iris.call_count == 2
    sensemaker.obj_standards_retriever.retrieve_data_for_grading.assert_has_calls(
        [
            call(sensemaker.oms_crud_tool, mock_node, required_attributes, required_relationships),
            call(sensemaker.oms_crud_tool, mock_node2, required_attributes, required_relationships),
        ]
    )
    sensemaker._get_required_iris.assert_has_calls([call(mock_node), call(mock_node2)])

    assert result == []


def test_get_required_iris_with_parent_class():
    """Test that parent class rubric is used when child class has no rubric."""
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_ontology_service = MagicMock()
    mock_retriever = MagicMock(spec=ObjectStandardsDataRetriever)
    mock_rubric = MagicMock()

    child_class_iri = "http://example.org/MilitaryJet"
    parent_class_iri = "http://example.org/Airplane"

    mock_node = MagicMock()
    mock_node.classIri = child_class_iri

    mock_ontology_service.get_node_ancestors_iris.return_value = [parent_class_iri]

    rubric_criteria = {parent_class_iri: {"ATTRIBUTES": ["attr1", "attr2"], "RELATIONSHIPS": ["rel1"]}}

    sensemaker = ObjectStandards(
        oms_crud_tool=mock_oms_crud_tool,
        ontology_service=mock_ontology_service,
        obj_standards_retriever=mock_retriever,
        obj_standards_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    required_iris = sensemaker._get_required_iris(mock_node)

    assert required_iris.attribute_iris == ["attr1", "attr2"]
    assert required_iris.relationship_iris == ["rel1"]
    mock_ontology_service.get_node_ancestors_iris.assert_called_once_with(mock_node)


def test_get_required_iris_no_rubric_after_max_levels():
    """Test that empty lists are returned when no rubric found after 5 levels."""
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_ontology_service = MagicMock()
    mock_retriever = MagicMock(spec=ObjectStandardsDataRetriever)
    mock_rubric = MagicMock()

    class_iri = "http://example.org/ClassIRI"
    mock_node = MagicMock()
    mock_node.classIri = class_iri

    # Return 4 ancestors so we check class_iri + 4 ancestors = 5 levels, none have rubrics
    mock_ontology_service.get_node_ancestors_iris.return_value = [f"http://example.org/parent_{i}" for i in range(4)]

    rubric_criteria = {}

    sensemaker = ObjectStandards(
        oms_crud_tool=mock_oms_crud_tool,
        ontology_service=mock_ontology_service,
        obj_standards_retriever=mock_retriever,
        obj_standards_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    required_iris = sensemaker._get_required_iris(mock_node)

    assert required_iris.attribute_iris == []
    assert required_iris.relationship_iris == []
    mock_ontology_service.get_node_ancestors_iris.assert_called_once_with(mock_node)


def test_get_required_iris_no_parent_class():
    """Test that empty lists are returned when no parent class exists."""
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_ontology_service = MagicMock()
    mock_retriever = MagicMock(spec=ObjectStandardsDataRetriever)
    mock_rubric = MagicMock()

    class_iri = "http://example.org/ClassIRI"
    mock_node = MagicMock()
    mock_node.classIri = class_iri

    mock_ontology_service.get_node_ancestors_iris.return_value = []

    rubric_criteria = {}

    sensemaker = ObjectStandards(
        oms_crud_tool=mock_oms_crud_tool,
        ontology_service=mock_ontology_service,
        obj_standards_retriever=mock_retriever,
        obj_standards_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    required_iris = sensemaker._get_required_iris(mock_node)

    assert required_iris.attribute_iris == []
    assert required_iris.relationship_iris == []
    mock_ontology_service.get_node_ancestors_iris.assert_called_once_with(mock_node)
