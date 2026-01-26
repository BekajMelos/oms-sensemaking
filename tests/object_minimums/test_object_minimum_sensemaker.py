from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    NodesNodes,
    OntologyClassOntologyClass,
    RelationshipRelationship,
)

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

    mock_nodes = MagicMock(spec=NodesNodes)
    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    mock_nodes.data = [mock_node]
    sensemaker.oms_crud_tool.get_nodes.return_value = mock_nodes

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

    sensemaker._get_required_iris = MagicMock(return_value=(required_attributes, required_relationships))

    mock_attributes = [{"attribute": "value"}]
    mock_relationships = [{"relationship": "value"}]

    sensemaker.obj_min_retriever.retrieve_data_for_grading.return_value = {
        "attributes": mock_attributes,
        "relationships": mock_relationships,
    }

    mock_grade = MagicMock()
    sensemaker._calculate_grade = MagicMock(return_value=mock_grade)

    result = sensemaker.process_data(rel_of_node)

    assert sensemaker.obj_min_retriever.retrieve_data_for_grading.call_count == 2
    assert sensemaker._get_required_iris.call_count == 2
    sensemaker.obj_min_retriever.retrieve_data_for_grading.assert_has_calls(
        [
            call(sensemaker.oms_crud_tool, mock_node, required_attributes, required_relationships),
            call(sensemaker.oms_crud_tool, mock_node2, required_attributes, required_relationships),
        ]
    )
    sensemaker._get_required_iris.assert_has_calls([call(mock_node.classIri), call(mock_node2.classIri)])

    assert result == []


def test_get_required_iris_with_parent_class():
    """Test that parent class rubric is used when child class has no rubric."""
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_retriever = MagicMock(spec=ObjectMinimumDataRetriever)
    mock_rubric = MagicMock()
    mock_ontology_client = MagicMock()

    child_class_iri = "http://example.org/MilitaryJet"
    parent_class_iri = "http://example.org/Airplane"

    # Create mock parent ontology class
    mock_parent_ontology_class = MagicMock(spec=OntologyClassOntologyClass)
    mock_parent_ontology_class.parentOntologyClasses = []

    # Create mock child ontology class with parent
    mock_child_ontology_class = MagicMock(spec=OntologyClassOntologyClass)
    mock_parent_ref = MagicMock()
    mock_parent_ref.iri = parent_class_iri
    mock_child_ontology_class.parentOntologyClasses = [mock_parent_ref]

    # Setup ontology client to return child class for child IRI, parent class for parent IRI
    def get_ontology_class_side_effect(iri):
        if iri == child_class_iri:
            return mock_child_ontology_class
        elif iri == parent_class_iri:
            return mock_parent_ontology_class
        return None

    mock_ontology_client.get_ontology_class.side_effect = get_ontology_class_side_effect

    # Rubric exists only for parent class
    rubric_criteria = {parent_class_iri: {"ATTRIBUTES": ["attr1", "attr2"], "RELATIONSHIPS": ["rel1"]}}

    sensemaker = ObjectMinimums(
        oms_crud_tool=mock_oms_crud_tool,
        obj_min_retriever=mock_retriever,
        obj_min_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    # Replace the ontology client with our mock
    sensemaker.ontology_client = mock_ontology_client

    required_attributes, required_relationships = sensemaker._get_required_iris(child_class_iri)

    assert required_attributes == ["attr1", "attr2"]
    assert required_relationships == ["rel1"]
    # Verify ontology client was called to get child class (to find its parent)
    mock_ontology_client.get_ontology_class.assert_called_with(child_class_iri)


def test_get_required_iris_no_rubric_after_max_levels():
    """Test that empty lists are returned when no rubric found after 5 levels."""
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_retriever = MagicMock(spec=ObjectMinimumDataRetriever)
    mock_rubric = MagicMock()
    mock_ontology_client = MagicMock()

    class_iri = "http://example.org/ClassIRI"

    # Setup ontology client to always return a class with a parent (creating a chain)
    # This creates an infinite chain, but we stop after 5 levels
    def get_ontology_class_side_effect(iri):
        mock_class = MagicMock(spec=OntologyClassOntologyClass)
        # Create a parent reference that points to a different IRI
        mock_parent = MagicMock()
        mock_parent.iri = f"{iri}_parent"
        mock_class.parentOntologyClasses = [mock_parent]
        return mock_class

    mock_ontology_client.get_ontology_class.side_effect = get_ontology_class_side_effect

    # No rubric exists for any class
    rubric_criteria = {}

    sensemaker = ObjectMinimums(
        oms_crud_tool=mock_oms_crud_tool,
        obj_min_retriever=mock_retriever,
        obj_min_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    # Replace the ontology client with our mock
    sensemaker.ontology_client = mock_ontology_client

    required_attributes, required_relationships = sensemaker._get_required_iris(class_iri)

    assert required_attributes == []
    assert required_relationships == []
    # Verify ontology client was called 4 times (for levels 0-3, checking up to 5 levels total)
    # Level 0: check class_iri (no ontology call needed, just dict lookup)
    # Level 1: check class_iri_parent (calls get_ontology_class for class_iri)
    # Level 2: check class_iri_parent_parent (calls get_ontology_class for class_iri_parent)
    # Level 3: check class_iri_parent_parent_parent (calls get_ontology_class for class_iri_parent_parent)
    # Level 4: check class_iri_parent_parent_parent_parent (calls get_ontology_class for class_iri_parent_parent_parent)
    # Total: 4 calls (one for each level after the first)
    assert mock_ontology_client.get_ontology_class.call_count == 4


def test_get_required_iris_no_parent_class():
    """Test that empty lists are returned when no parent class exists."""
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
    mock_retriever = MagicMock(spec=ObjectMinimumDataRetriever)
    mock_rubric = MagicMock()
    mock_ontology_client = MagicMock()

    class_iri = "http://example.org/ClassIRI"

    # Create mock ontology class with no parent
    mock_ontology_class = MagicMock(spec=OntologyClassOntologyClass)
    mock_ontology_class.parentOntologyClasses = []

    mock_ontology_client.get_ontology_class.return_value = mock_ontology_class

    # No rubric exists for the class
    rubric_criteria = {}

    sensemaker = ObjectMinimums(
        oms_crud_tool=mock_oms_crud_tool,
        obj_min_retriever=mock_retriever,
        obj_min_rubric=mock_rubric,
        rubric_criteria=rubric_criteria,
    )

    # Replace the ontology client with our mock
    sensemaker.ontology_client = mock_ontology_client

    required_attributes, required_relationships = sensemaker._get_required_iris(class_iri)

    assert required_attributes == []
    assert required_relationships == []
    # Verify ontology client was called once (to check for parent after level 0 finds no rubric)
    mock_ontology_client.get_ontology_class.assert_called_once_with(class_iri)
