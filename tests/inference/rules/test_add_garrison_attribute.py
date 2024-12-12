import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence
from oms_sdk.generated.generated_graphql_client.input_types import (
    CreateAttributeInput,
)
from oms_sdk.generated.generated_graphql_client.node import NodeNode
from oms_sdk.generated.generated_graphql_client.relationship import RelationshipRelationship
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.add_garrison_attribute import AddOutOfGarrisonAttribute
from oms_sensemaking.inference.rules.rule_context import RuleContext


# Sample Attributes
@pytest.fixture
def initial_attr(mocker: MockerFixture):
    """
    An initial attribute to be evaluated
    """
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "uuid1"
    attr.acm = DEFAULT_ACM
    attr.attributeIri = SETTINGS.inference_add_garrison_attribute_iri
    attr.attributeName = SETTINGS.inference_add_garrison_attribute_iri.split("/")[-1]
    attr.attributeValue = "Initial Attribute"
    attr.attributeType = AttributeType.BOOLEAN
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "0cc17447-b1f8-48e8-ae30-f9031f250b5d" # Observational Node
    attr.geo = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "coordinates": [
                    -2.86242139203938,
                    18.68484166661493
                ],
            "type": "Point"
        }}]
    }

    return attr

@pytest.fixture
def final_attr(mocker: MockerFixture):
    """
    A final attribute to be evaluated
    """
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "uuid2"
    attr.acm = DEFAULT_ACM
    attr.attributeIri = SETTINGS.inference_garrison_location_iri
    attr.attributeName = SETTINGS.inference_garrison_location_iri.split("/")[-1]
    attr.attributeValue = "some attr name"
    attr.attributeType = AttributeType.BOOLEAN
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "dd7763a6-dad4-46d7-acfa-d23a648eb143" # Base Node
    attr.geo = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "coordinates": [
                    -5.632561898769694,
                    23.307540107821012
                ],
            "type": "Point"
        }}]
    }

    return attr

# Sample Relationships
@pytest.fixture
def observational_node_relationship(mocker: MockerFixture):
    """
    An observational node relationship to be evaluated
    """
    relationship = mocker.Mock(spec=RelationshipRelationship)
    relationship.id = "7526268d-b736-4341-b30e-098139d674cd" # Observational Node Relationship
    relationship.objectPropertyIris = [SETTINGS.inference_participated_in_iri]
    #relationship.startNodeId = "0cc17447-b1f8-48e8-ae30-f9031f250b5d" # Observational Node
    #relationship.endNodeId = "68e2f92d-125f-42ca-8197-27beda61542f" # Primary Node
    # Observational Node + Primary Node
    relationship.relatedNodeIds=["0cc17447-b1f8-48e8-ae30-f9031f250b5d", "68e2f92d-125f-42ca-8197-27beda61542f"]
    relationship.name = "TEST 1"

    return relationship

@pytest.fixture
def primary_node_relationship(mocker: MockerFixture):
    """
    A primary node relationship relationship to be evaluated
    """
    relationship = mocker.Mock(spec=RelationshipRelationship)
    relationship.id = "8236af0c-0c7f-432a-a098-80cc10c15ab6" # Primary Node Relationship
    relationship.objectPropertyIris = [SETTINGS.inference_garrison_location_iri]
    #relationship.startNodeId = "68e2f92d-125f-42ca-8197-27beda61542f" # Primary Node
    #relationship.endNodeId = "dd7763a6-dad4-46d7-acfa-d23a648eb143" # Base Node
    # Base Node
    relationship.relatedNodeIds=["68e2f92d-125f-42ca-8197-27beda61542f", "dd7763a6-dad4-46d7-acfa-d23a648eb143"]
    relationship.name = "TEST 2"

    return relationship

# Sample Nodes
@pytest.fixture
def observational_node(mocker: MockerFixture):
    """
    An observational node to be evaluated
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "0cc17447-b1f8-48e8-ae30-f9031f250b5d" # Observational Node
    node.name = "Observational Node"
    node.geoQuery = "some query"
    node.realrelationships = observational_node_relationship
    node.tier = "OBSERVATIONAL"

    return node

@pytest.fixture
def primary_node(mocker: MockerFixture):
    """
    A primary node to be evaluated
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "68e2f92d-125f-42ca-8197-27beda61542f" # Primary Node
    node.name = "Primary Node"
    node.geoQuery = "some query"
    node.relationships = primary_node_relationship
    node.tier = "PRIMARY"

    return node

@pytest.fixture
def base_node(mocker: MockerFixture):
    """
    A base node to be evaluated
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "dd7763a6-dad4-46d7-acfa-d23a648eb143" # Base Node
    node.name = "Base Node"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "DERIVATIVE" #idk what this should be
    node.attributes = [final_attr]

    return node

# Tests
def test_evaluate_input(initial_attr):
    """Test to verify the attribute has a geo"""
    rule = AddOutOfGarrisonAttribute("some name")
    assert rule.evaluate(RuleContext(attribute=initial_attr)) is True

def test_action_creates_attribute(mocker: MockerFixture,
                                  initial_attr,
                                  final_attr,
                                  observational_node_relationship,
                                  primary_node_relationship,
                                  observational_node,
                                  primary_node,
                                  base_node):
    mock = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")

    # Mock Final Attribute
    mock_get_final_attr = mocker.patch("oms_sensemaking.clients.oms_client.get_attributes")
    mock_get_final_attr.return_value = final_attr


    # Node mocks
    mock_get_nodes = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock_nodes = {
        "0cc17447-b1f8-48e8-ae30-f9031f250b5d": observational_node,
        "68e2f92d-125f-42ca-8197-27beda61542f": primary_node,
        "dd7763a6-dad4-46d7-acfa-d23a648eb143": base_node,
    }

    def get_nodes_side_effect(query):
        node_id = query.ids[0]
        return mock_nodes.get(node_id)

    mock_get_nodes.side_effect = get_nodes_side_effect


    # Relationship mocks
    mock_get_relationships = mocker.patch("oms_sensemaking.clients.oms_client.get_relationships")
    mock_relationships = {
        SETTINGS.inference_participated_in_iri: observational_node_relationship,
        SETTINGS.inference_garrison_location_iri: primary_node_relationship
    }

    def get_relationships_side_effect(query):
        query_object_properties = query.hasMatch.objectPropertyIris
        query_related_node_ids = query.hasMatch.relatedNodeIds
        matching_relationships = [
            relationship
            for relationship in mock_relationships.values()
            if (
                set(query_object_properties).intersection(relationship.objectPropertyIris)
                and set(query_related_node_ids).intersection(relationship.relatedNodeIds)
            )
        ]
        return matching_relationships

    mock_get_relationships.side_effect = get_relationships_side_effect

    rule = AddOutOfGarrisonAttribute("some name")
    rule.action(RuleContext(attribute=initial_attr))
    mock.assert_called_once_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_is_garrison_at_iri,
            attributeValue="Yes",
            attributeType=AttributeType.STRING,
            confidence=initial_attr.confidence,
            sourceId=initial_attr.sourceId,
            acm=initial_attr.acm,
            isMutable=False,
            tags=SETTINGS.inference_tags
        )
    )
