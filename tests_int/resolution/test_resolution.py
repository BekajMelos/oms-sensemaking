"""Tests for resolution sensemaker."""

import json
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    CreateRelationshipCreateRelationship,
    NodeNode,
    NodesNodes,
    RelationshipRelationship,
    RelationshipsRelationships,
)
from oms_sdk.generated.generated_graphql_client.enums import ObjectTier
from sqlalchemy import select

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.models.sensemaking import Finding, FindingType
from oms_sensemaking.resolution.sensemaker import ResolutionSensemaker
from tests_int.conftest import rollup_unclass_acm_3_0

BE_NUMBER_IRI = "https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber"
BE_NUMBER = "ABCD1234"
OSUFFIX_IRI = "https://foundry.ai.mil/ontology/4901-001/hasOSuffix"
OSUFFIX = "12345"
EQUIPMENT_CODE_IRI = "https://foundry.ai.mil/ontology/meks/p-0000000050"
EQUIPMENT_CODE = "eqpCode123"


@pytest.fixture
def tester_db():
    original_facility_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="original_facility_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )
    original_be_number_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=BE_NUMBER_IRI,
        attributeValue=BE_NUMBER,
        nodeId=original_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    original_osuffix_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=OSUFFIX_IRI,
        attributeValue=OSUFFIX,
        nodeId=original_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    original_equipment_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="original_equipment_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/EquipmentItem",
    )
    original_equipment_code_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=EQUIPMENT_CODE_IRI,
        attributeValue=EQUIPMENT_CODE,
        nodeId=original_equipment_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    facility_node_empty_string = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="facility_empty_string",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )
    empty_string_be_num_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=BE_NUMBER_IRI,
        attributeValue="",
        nodeId=facility_node_empty_string.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    empty_string_osuffix_num_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=OSUFFIX_IRI,
        attributeValue="",
        nodeId=facility_node_empty_string.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    facility_node_mismatch_keys = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="facility_mismatch_keys",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )
    mismatch_key_be_num_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=BE_NUMBER_IRI,
        attributeValue="12345678",
        nodeId=facility_node_mismatch_keys.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    mismatch_key_osuffix_num_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=OSUFFIX_IRI,
        attributeValue="ABCD",
        nodeId=facility_node_mismatch_keys.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )

    return [
        original_facility_node,
        original_be_number_attribute,
        original_osuffix_attribute,
        original_equipment_node,
        original_equipment_code_attribute,
        facility_node_empty_string,
        empty_string_be_num_attribute,
        empty_string_osuffix_num_attribute,
        facility_node_mismatch_keys,
        mismatch_key_be_num_attribute,
        mismatch_key_osuffix_num_attribute,
    ]


@pytest.fixture
def facility_dual_criteria_config():
    """
    Test-only config that allows matching Facilities via either:
      1) BE_NUMBER + OSUFFIX (primary), or
      2) SK-only (alternate).
    """
    sk_iri = "https://foundry.ai.mil/ontology/4901-001/hasMIBDBFacilitySurrogateKey"

    return {
        "https://foundry.ai.mil/ontology/4901-001/Facility": [
            [BE_NUMBER_IRI, OSUFFIX_IRI],
            [sk_iri],
        ]
    }


def test_resolution_sensemaker(db, mock_source, tester_db):
    """Test Resolution Sensemaker"""
    with open(SETTINGS.duplicate_object_iris_file_path) as fd:
        duplicate_object_iris = json.load(fd)
    mock_oms_crud_tool = mock.MagicMock(spec=OmsCrudTool)
    new_facility_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="new_facility_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )
    new_equipment_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="new_equipment_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/EquipmentItem",
    )
    # Get Relationships Mock
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(data=[])
    mock_response = CreateRelationshipCreateRelationship.model_construct(id=uuid4())
    mock_oms_crud_tool.create_relationship.return_value = mock_response

    # Get Node Mock
    mock_oms_crud_tool.get_node.return_value = new_facility_node

    # Test unsupported attribute is ignored
    unsupported_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="test",
        attributeValue="test",
        nodeId=new_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(unsupported_attribute) == []

    # Test Failure. Irrelevant attribute IRI
    new_irrelevant_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="bleh",
        attributeValue=EQUIPMENT_CODE,
        nodeId=new_equipment_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_irrelevant_attribute) == []

    # Test Failure. Attribute not pointing to a node
    new_no_node_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=EQUIPMENT_CODE_IRI,
        attributeValue=EQUIPMENT_CODE,
        nodeId=None,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_no_node_attribute) == []

    # Test Failure. BE_NUMBER given but no OSUFFIX in DB. Criteria not met
    new_be_number_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=BE_NUMBER_IRI,
        attributeValue=BE_NUMBER,
        nodeId=new_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_be_number_attribute) == []

    # Test Failure. Matching facility nodes with be number and osuffix. Criteria met but no matching nodes
    new_osuffix_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=OSUFFIX_IRI,
        attributeValue=OSUFFIX,
        nodeId=new_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    # mock osuffix already existing and be_number being sent
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [new_osuffix_attribute]
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[])
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_be_number_attribute) == []

    # Test Success. Matching facility nodes with be number and osuffix. Criteria met with matching nodes
    # mock osuffix already existing and be_number being sent, and matching nodes being returned
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[tester_db[0]])

    dups = ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_be_number_attribute)
    assert len(dups) == 1

    # Test Success. Matching equipment nodes with be number and osuffix. Criteria met with matching nodes
    new_equipment_code_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=EQUIPMENT_CODE_IRI,
        attributeValue=EQUIPMENT_CODE,
        nodeId=new_equipment_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    # mock equipment code being sent, and matching nodes being returned
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[tester_db[3]])
    mock_oms_crud_tool.get_node.return_value = new_equipment_node

    dups = ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_equipment_code_attribute)
    assert len(dups) == 1

    # Test Failure. Getting the same data again should not return new duplicates
    # mock has_already_ran seeing the relationship
    new_relationship = RelationshipRelationship.model_construct(
        name=SETTINGS.resolution_relationship_name,
        startNodeId=new_facility_node.id,
    )
    mock_oms_crud_tool.get_node.return_value = new_facility_node
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[tester_db[0]])
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(
        data=[new_relationship]
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_be_number_attribute) == []

    # check that duplicates exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.RESOLUTION_DUPLICATE.value))
        .scalars()
        .all()
    )

    assert len(findings) == 2
    assert findings[0].acm == rollup_unclass_acm_3_0()
    start_nodes = [finding.finding_data["start_node_id"] for finding in findings]
    end_nodes = [finding.finding_data["end_node_id"] for finding in findings]
    assert str(new_equipment_node.id) in start_nodes
    assert str(new_facility_node.id) in start_nodes
    assert findings[1].acm == rollup_unclass_acm_3_0()
    assert str(tester_db[3].id) in end_nodes
    assert str(tester_db[0].id) in end_nodes


def test_resolution_matches_using_alternate_criteria_set(db, mock_source, tester_db, facility_dual_criteria_config):
    """
    Integration test that proves the Resolution Sensemaker can match
    duplicates using any valid criteria set (OR semantics), not only
    the primary BE+OSUFFIX identity. Specifically validates that an
    SK-only match is sufficient when configured as an alternate key.
    """

    mock_oms_crud_tool = mock.MagicMock(spec=OmsCrudTool)

    # New facility that only has SK
    new_facility_sk = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="new_facility_sk",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )

    sk_iri = "https://foundry.ai.mil/ontology/4901-001/hasMIBDBFacilitySurrogateKey"
    sk_value = "SK-123"

    new_sk_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=sk_iri,
        attributeValue=sk_value,
        nodeId=new_facility_sk.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )

    # No existing relationships (has_already_ran = False)
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(data=[])

    # Class lookup
    mock_oms_crud_tool.get_node.return_value = new_facility_sk

    # Node has no other attributes (pure SK case)
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = []

    # Pretend there is an existing Facility in DB with same SK
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(
        data=[tester_db[0]]  # existing facility from tester_db
    )

    sensemaker = ResolutionSensemaker(facility_dual_criteria_config, mock_oms_crud_tool)
    sensemaker.save_findings = mock.MagicMock()
    findings = sensemaker.execute(new_sk_attribute)

    # Assert: SK-only match should work
    assert len(findings) == 1

    finding = findings[0]
    assert finding.start_node_id == new_facility_sk.id
    assert finding.end_node_id == tester_db[0].id


def test_resolution_no_relationship_empty_string(db, mock_source, tester_db):
    """Test Resolution Sensemaker"""
    with open(SETTINGS.duplicate_object_iris_file_path) as fd:
        duplicate_object_iris = json.load(fd)
    mock_oms_crud_tool = mock.MagicMock(spec=OmsCrudTool)
    facility_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="facility_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )
    # Get Relationships Mock
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(data=[])

    # Get Node Mock
    mock_oms_crud_tool.get_node.return_value = facility_node

    facility_be_num_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=BE_NUMBER_IRI,
        attributeValue="",
        nodeId=facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    facility_osuffix_num_attribute = AttributeAttribute.model_construct(
        attributeIri=OSUFFIX_IRI, attributeValue="", nodeId=facility_node.id, sourceId=uuid4(), acm=DEFAULT_ACM
    )

    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [facility_osuffix_num_attribute]
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(facility_be_num_attribute) == []

    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.RESOLUTION_DUPLICATE.value))
        .scalars()
        .all()
    )

    assert len(findings) == 0


def test_resolution_no_relationship_mismatch_keys(db, mock_source, tester_db):
    """Test Resolution Sensemaker"""
    with open(SETTINGS.duplicate_object_iris_file_path) as fd:
        duplicate_object_iris = json.load(fd)
    mock_oms_crud_tool = mock.MagicMock(spec=OmsCrudTool)
    facility_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="facility_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )
    # Get Relationships Mock
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(data=[])

    # Get Node Mock
    mock_oms_crud_tool.get_node.return_value = facility_node

    facility_be_num_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=BE_NUMBER_IRI,
        attributeValue="876564321",
        nodeId=facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    facility_osuffix_num_attribute = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=OSUFFIX_IRI,
        attributeValue="ABCD",
        nodeId=facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )

    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[])
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [facility_osuffix_num_attribute]
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(facility_be_num_attribute) == []

    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.RESOLUTION_DUPLICATE.value))
        .scalars()
        .all()
    )

    assert len(findings) == 0
