from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    CompliantObjectInput,
    CreateObjectStandardsInput,
    NodesNodes,
    NodesNodesData,
    ObjectStandardsObjectStandards,
    ObjectStandardsObjectStandardsData,
    ObjectStandardsViolationInput,
    ObjectType,
    RelationshipRelationship,
    UpdateObjectStandardsInput,
    ViolationType,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.object_standards.object_standards_models import ObjectStandardsGrade, RequiredIris
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
    sensemaker.obj_standards_rubric.grade = MagicMock(return_value=mock_grade)

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
    sensemaker.obj_standards_rubric.grade = MagicMock(return_value=mock_grade)

    result = sensemaker.process_data(attribute_of_node)

    sensemaker.obj_standards_retriever.retrieve_data_for_grading.assert_called_once_with(
        sensemaker.oms_crud_tool, mock_node, required_attributes, required_relationships
    )

    sensemaker.obj_standards_rubric.grade.assert_called_once_with(mock_attributes, mock_relationships)
    assert result == []


@patch("oms_sensemaking.object_standards.sensemaker.aac_client.get_acm_rollup")
def test_process_data_rel_passed_in(mock_aac_client, sensemaker):
    rel_of_node = MagicMock(spec=RelationshipRelationship)
    rel_of_node.startNodeId = str(uuid4())
    rel_of_node.endNodeId = str(uuid4())

    mock_nodes = MagicMock(spec=NodesNodes)
    mock_node = MagicMock()
    mock_node.classIri = "http://example.org/ClassIRI"
    mock_node.acm = DEFAULT_ACM
    mock_node2 = MagicMock()
    mock_node2.classIri = "http://example.org/ClassIRI"
    mock_node2.acm = DEFAULT_ACM
    mock_nodes.data = [mock_node, mock_node2]
    sensemaker.oms_crud_tool.get_nodes.return_value = mock_nodes

    mock_obj_stds = MagicMock(spec=ObjectStandardsObjectStandards)
    mock_obj_stds.data = []
    sensemaker.oms_crud_tool.get_object_standards.return_value = mock_obj_stds

    required_attributes = ["iri1", "iri2"]
    required_relationships = ["relIri1", "relIri2"]

    sensemaker._get_required_iris = MagicMock(
        return_value=RequiredIris(attribute_iris=required_attributes, relationship_iris=required_relationships)
    )

    mock_attr = MagicMock(spec=AttributeAttribute)
    mock_attr.acm = DEFAULT_ACM
    mock_rel = MagicMock(spec=RelationshipRelationship)
    mock_rel.acm = DEFAULT_ACM
    mock_attributes = [mock_attr]
    mock_relationships = [mock_rel]

    sensemaker.obj_standards_retriever.retrieve_data_for_grading.return_value = {
        "attributes": mock_attributes,
        "relationships": mock_relationships,
    }
    mock_aac_client.return_value = DEFAULT_ACM

    mock_grade = MagicMock()
    sensemaker.obj_standards_rubric.grade = MagicMock(return_value=mock_grade)

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


def test_generate_summary_string(sensemaker):
    float_score = 0.5
    ratio_score = "1/2"
    len_violations = 1
    len_compliant_fields = 1
    summary = sensemaker.generate_summary_string(float_score, ratio_score, len_violations, len_compliant_fields)
    assert summary == (
        "This object has an Object Standards score of 0.5 (1/2). "
        "This object has 1 violation(s) and 1 compliant object(s)."
    )


def test_publish_results_to_atoms_update(sensemaker):
    fixed = datetime(2025, 5, 17, 14, 30, tzinfo=timezone.utc)
    with patch("oms_sensemaking.object_standards.sensemaker.datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed
        existing_obj_standard = MagicMock(spec=ObjectStandardsObjectStandardsData)
        existing_obj_standard.id = uuid4()

        mock_node = MagicMock(spec=NodesNodesData)
        mock_node.id = uuid4()

        rolled_up_acm = DEFAULT_ACM

        violation = ObjectStandardsViolationInput(
            objectType=ObjectType.ATTRIBUTE, iri="attr_iri", violationType=ViolationType.MISSING, description="str"
        )

        compliant_object = CompliantObjectInput(id=uuid4(), objectType=ObjectType.ATTRIBUTE)

        grade = MagicMock(spec=ObjectStandardsGrade)
        grade.float_score = 0.5
        grade.ratio = "1/2"
        grade.violations = [violation]
        grade.compliant_fields = [compliant_object]

        summary = (
            "This object has an Object Standards score of 0.5 (1/2). "
            "This object has 1 violation(s) and 1 compliant object(s)."
        )

        sensemaker.publish_results_to_atoms(mock_node, [existing_obj_standard], rolled_up_acm, grade)

        sensemaker.oms_crud_tool.update_object_standards.assert_called_with(
            UpdateObjectStandardsInput(
                id=existing_obj_standard.id,
                acm=rolled_up_acm,
                summary=summary,
                score=grade.float_score,
                violations=grade.violations,
                compliantObjects=grade.compliant_fields,
                timestamp=fixed,
            )
        )


def test_publish_results_to_atoms_create(sensemaker):
    fixed = datetime(2025, 5, 17, 14, 30, tzinfo=timezone.utc)
    with patch("oms_sensemaking.object_standards.sensemaker.datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed

        mock_node = MagicMock(spec=NodesNodesData)
        mock_node.id = uuid4()

        rolled_up_acm = DEFAULT_ACM

        violation = ObjectStandardsViolationInput(
            objectType=ObjectType.ATTRIBUTE, iri="attr_iri", violationType=ViolationType.MISSING, description="str"
        )

        compliant_object = CompliantObjectInput(id=uuid4(), objectType=ObjectType.ATTRIBUTE)

        grade = MagicMock(spec=ObjectStandardsGrade)
        grade.float_score = 0.5
        grade.ratio = "1/2"
        grade.violations = [violation]
        grade.compliant_fields = [compliant_object]

        summary = (
            "This object has an Object Standards score of 0.5 (1/2). "
            "This object has 1 violation(s) and 1 compliant object(s)."
        )

        sensemaker.publish_results_to_atoms(mock_node, [], rolled_up_acm, grade)

        sensemaker.oms_crud_tool.create_object_standards.assert_called_with(
            CreateObjectStandardsInput(
                acm=rolled_up_acm,
                tags=SETTINGS.object_standards_settings.tags,
                nodeId=mock_node.id,
                summary=summary,
                score=grade.float_score,
                violations=grade.violations,
                compliantObjects=grade.compliant_fields,
                timestamp=fixed,
                standardsVersion=SETTINGS.object_standards_settings.playbook_version,
            )
        )
