import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.node import NodeNode
from oms_sdk.generated.generated_graphql_client.relationship import RelationshipRelationship
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeQuery,
    CreateAttributeInput,
    StringQuery,
)
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.add_has_name_attribute import AddHasNameAttribute
from oms_sensemaking.inference.rules.add_garrison_attribute import AddGarrisonAttribute
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
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd" # Dunno what this is
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
    attr.attributeIri = SETTINGS.inference_add_garrison_attribute_iri
    attr.attributeName = SETTINGS.inference_add_garrison_attribute_iri.split("/")[-1]
    attr.attributeValue = "some attr name"
    attr.attributeType = AttributeType.BOOLEAN
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd" # Dunno what this is
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
    relationship.id = "uuid1" # dunno if this is necessary
    relationship.objectPropertyIri = SETTINGS.inference_participated_in_iri
    relationship.startNodeId = "0cc17447-b1f8-48e8-ae30-f9031f250b5d" # Observational Node
    relationship.endNodeId = "68e2f92d-125f-42ca-8197-27beda61542f" # Primary Node

    return relationship

@pytest.fixture
def primary_node_relationship(mocker: MockerFixture):
    """
    A primary node relationship relationship to be evaluated
    """
    relationship = mocker.Mock(spec=RelationshipRelationship)
    relationship.id = "uuid2" # dunno if this is necessary
    relationship.objectPropertyIri = SETTINGS.inference_garrison_location_iri
    relationship.startNodeId = "68e2f92d-125f-42ca-8197-27beda61542f" # Primary Node
    relationship.endNodeId = "dd7763a6-dad4-46d7-acfa-d23a648eb143" # Base Node

    return relationship

# Sample Nodes
@pytest.fixture
def observational_node(mocker: MockerFixture):
    """
    An observational node to be evaluated
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "0cc17447-b1f8-48e8-ae30-f9031f250b5d" # Observational Node
    node.name = "TEST"
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
    node.name = "TEST"
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
    node.name = "TEST"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "PRIMARY" #idk what this should be
    node.attributes = [final_attr]

    return node

def test_evaluate_none_input():
    """Test to verify we only run the rule against attributes"""
    print("********************START TEST********************")
    rule = AddGarrisonAttribute("some name")
    assert not rule.evaluate(RuleContext()), "should only run for attributes"

def test_action_creates_attribute(mocker: MockerFixture, initial_attr, final_attr, observational_node_relationship, primary_node_relationship, observational_node, primary_node, base_node):
    print("*********************START ACTION TEST************************")
    mock = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")
    
    # Mock Final Attribute
    mock_create_final_attr = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")
    mock_get_final_attr = mocker.patch("oms_sensemaking.clients.oms_client.get_attribute")
    mock_create_final_attr.return_value = final_attr
    mock_get_final_attr.return_value = final_attr

    # Mock Observational Node Relationship
    mock_create_observational_node_relationship = mocker.patch("oms_sensemaking.clients.oms_client.create_relationship")
    mock_get_observational_node_relationship = mocker.patch("oms_sensemaking.clients.oms_client.get_relationship")
    mock_create_observational_node_relationship.return_value = observational_node_relationship
    mock_get_observational_node_relationship.return_value = observational_node_relationship

    # Mock Primary Node Relationship
    mock_create_primary_node_relationship = mocker.patch("oms_sensemaking.clients.oms_client.create_relationship")
    mock_get_primary_node_relationship = mocker.patch("oms_sensemaking.clients.oms_client.get_relationship")
    mock_create_primary_node_relationship.return_value = primary_node_relationship
    mock_get_primary_node_relationship.return_value = primary_node_relationship

    # Mock Observational Node
    mock_create_observational_node = mocker.patch("oms_sensemaking.clients.oms_client.create_node")
    mock_get_observational_node = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock_create_observational_node.return_value = observational_node
    mock_get_observational_node.return_value = observational_node

    # Mock Primary Node
    mock_create_primary_node = mocker.patch("oms_sensemaking.clients.oms_client.create_node")
    mock_get_primary_node = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock_create_primary_node.return_value = primary_node
    mock_get_primary_node.return_value = primary_node

    # Mock Base Node
    mock_create_base_node = mocker.patch("oms_sensemaking.clients.oms_client.create_node")
    mock_get_base_node = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock_create_base_node.return_value = base_node
    mock_get_base_node.return_value = base_node


    print("test 1")
    rule = AddGarrisonAttribute("some name")
    print("test 2")
    rule.action(RuleContext(attribute=initial_attr))
    print("test 3")
    mock.assert_called_once_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue="true",
            attributeType=AttributeType.BOOLEAN,
            confidence=initial_attr.confidence,
            sourceId=initial_attr.sourceId,
            nodeId=initial_attr.nodeId,
            acm=initial_attr.acm,
            tags=SETTINGS.inference_tags,
        )
    )
