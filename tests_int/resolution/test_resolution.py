"""Tests for resolution sensemaker."""

import json
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
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
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility"
    )
    original_be_number_attribute = AttributeAttribute.model_construct(
        attributeIri=BE_NUMBER_IRI,
        attributeValue=BE_NUMBER,
        nodeId=original_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    original_osuffix_attribute = AttributeAttribute.model_construct(
        attributeIri=OSUFFIX_IRI,
        attributeValue=OSUFFIX,
        nodeId=original_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    original_equipment_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="original_equipment_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/EquipmentItem"
    )
    original_equipment_code_attribute = AttributeAttribute.model_construct(
        attributeIri=EQUIPMENT_CODE_IRI,
        attributeValue=EQUIPMENT_CODE,
        nodeId=original_equipment_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )

    return [original_facility_node,
           original_be_number_attribute,
           original_osuffix_attribute,
           original_equipment_node,
           original_equipment_code_attribute]


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
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility"
    )
    new_equipment_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="new_equipment_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/EquipmentItem"
    )
    # Get Relationships Mock
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(data=[])

    # Get Node Mock
    mock_oms_crud_tool.get_node.return_value = new_facility_node

    # Test unsupported attribute is ignored
    unsupported_attribute = AttributeAttribute.model_construct(
        attributeIri="test",
        attributeValue="test",
        nodeId=new_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(unsupported_attribute) == []

    # Test Failure. Irrelevant attribute IRI
    new_irrelevant_attribute = AttributeAttribute.model_construct(
        attributeIri="bleh",
        attributeValue=EQUIPMENT_CODE,
        nodeId=new_equipment_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_irrelevant_attribute) == []

    # Test Failure. Attribute not pointing to a node
    new_no_node_attribute = AttributeAttribute.model_construct(
        attributeIri=EQUIPMENT_CODE_IRI,
        attributeValue=EQUIPMENT_CODE,
        nodeId=None,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_no_node_attribute) == []

    # Test Failure. BE_NUMBER given but no OSUFFIX in DB. Criteria not met
    new_be_number_attribute = AttributeAttribute.model_construct(
        attributeIri=BE_NUMBER_IRI,
        attributeValue=BE_NUMBER,
        nodeId=new_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_be_number_attribute) == []


    # Test Failure. Matching facility nodes with be number and osuffix. Criteria met but no matching nodes
    new_osuffix_attribute = AttributeAttribute.model_construct(
        attributeIri=OSUFFIX_IRI,
        attributeValue=OSUFFIX,
        nodeId=new_facility_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
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
        attributeIri=EQUIPMENT_CODE_IRI,
        attributeValue=EQUIPMENT_CODE,
        nodeId=new_equipment_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
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
        data=[new_relationship])
    assert ResolutionSensemaker(duplicate_object_iris, mock_oms_crud_tool).execute(new_be_number_attribute) == []

    # check that duplicates exist in Findings table
    findings = db.execute(
        select(Finding).filter(
            Finding.finding_type == FindingType.RESOLUTION_DUPLICATE.value
            )
        ).scalars().all()

    assert len(findings) == 2
    assert findings[0].acm == tester_db[1].acm
    assert findings[0].finding_data["start_node_id"] == str(new_facility_node.id)
    assert findings[0].finding_data["end_node_id"] == str(tester_db[0].id)
    assert findings[1].acm == tester_db[4].acm
    assert findings[1].finding_data["start_node_id"] == str(new_equipment_node.id)
    assert findings[1].finding_data["end_node_id"] == str(tester_db[3].id)
