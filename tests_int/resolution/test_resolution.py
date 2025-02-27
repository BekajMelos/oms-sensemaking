"""Tests for resolution sensemaker."""

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

BE_NUMBER_IRI = "https://foundry.ai.mil/MIDB_GST/v1/BE_Number"
BE_NUMBER = "ABCD1234"
OSUFFIX_IRI = "https://foundry.ai.mil/DICO/v3.1.0/OSuffix"
OSUFFIX = "12345"


@pytest.fixture
def tester_db():

    original_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="original_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/NIEM/v5.2/FacilityType"
    )
    original_be_number_attribute = AttributeAttribute.model_construct(
        attributeIri=BE_NUMBER_IRI,
        attributeValue=BE_NUMBER,
        nodeId=original_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    original_osuffix_attribute = AttributeAttribute.model_construct(
        attributeIri=OSUFFIX_IRI,
        attributeValue=OSUFFIX,
        nodeId=original_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )

    return original_node, original_be_number_attribute, original_osuffix_attribute


def test_resolution_sensemaker(db, mock_source, tester_db):
    """Test Resolution Sensemaker"""

    mock_oms_crud_tool = mock.MagicMock(spec=OmsCrudTool)
    new_node = NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="new_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/NIEM/v5.2/FacilityType"
    )

    # Get Relationships Mock
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(data=[])

    # Test unsupported attribute is ignored
    unsupported_attribute = AttributeAttribute.model_construct(
        attributeIri="test",
        attributeValue="test",
        nodeId=new_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    assert ResolutionSensemaker(mock_oms_crud_tool).execute(unsupported_attribute) == []


    # Test Failure. BE_NUMBER given but no OSUFFIX in DB. Criteria not met
    new_be_number_attribute = AttributeAttribute.model_construct(
        attributeIri=BE_NUMBER_IRI,
        attributeValue=BE_NUMBER,
        nodeId=new_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    assert ResolutionSensemaker(mock_oms_crud_tool).execute(new_be_number_attribute) == []


    # Test Failure. Matching nodes with be number and osuffix. Criteria met but no matching nodes
    new_osuffix_attribute = AttributeAttribute.model_construct(
        attributeIri=OSUFFIX_IRI,
        attributeValue=OSUFFIX,
        nodeId=new_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )
    # mock osuffix already existing and be_number being sent
    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [new_osuffix_attribute]
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[])
    assert ResolutionSensemaker(mock_oms_crud_tool).execute(new_be_number_attribute) == []


    # Test Success. Matching nodes with be number and osuffix. Criteria met with matching nodes
    # mock osuffix already existing and be_number being sent, and matching nodes being returned
    mock_oms_crud_tool.get_nodes.return_value = NodesNodes.model_construct(data=[tester_db[0]])

    dups = ResolutionSensemaker(mock_oms_crud_tool).execute(new_be_number_attribute)
    assert len(dups) == 1


    # Test Failure. Getting the same data again should not return new duplicates
    # mock has_already_ran seeing the relationship
    new_relationship = RelationshipRelationship.model_construct(
        name=SETTINGS.resolution_relationship_name,
        startNodeId=new_node.id,
    )
    mock_oms_crud_tool.get_relationships.return_value = RelationshipsRelationships.model_construct(
        data=[new_relationship])
    assert ResolutionSensemaker(mock_oms_crud_tool).execute(new_be_number_attribute) == []

    # check that duplicates exist in Findings table
    findings = db.execute(
        select(Finding).filter(
            Finding.finding_type == FindingType.RESOLUTION_DUPLICATE.value
            )
        ).scalars().all()

    assert len(findings) == 1
    assert findings[0].acm == tester_db[1].acm
    assert findings[0].finding_data["start_node_id"] == str(new_node.id)
    assert findings[0].finding_data["end_node_id"] == str(tester_db[0].id)
