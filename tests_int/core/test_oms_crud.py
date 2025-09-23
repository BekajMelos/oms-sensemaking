import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeQuery,
    AttributeType,
    Confidence,
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
    NodeQuery,
    ObjectTier,
    RelationshipQuery,
    StringQuery,
    UpdateAttributeInput,
    UpdateNodeInput,
    UpdateRelationshipInput,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool

oms_crud_tool = OmsCrudTool()
person_node_iri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
work_for_relationship_iri = SETTINGS.resolution_relationship_iri
test_node_name1 = "test_node_name1"
test_node_name2 = "test_node_name2"
test_attribute_name1 = "test_attribute_name1"
test_attribute_name2 = "test_attribute_name2"
test_relationship_name1 = "test_relationship_name1"
test_relationship_name2 = "test_relationship_name2"


@pytest.fixture(scope="function")
def test_node1():
    node1 = oms_crud_tool.create_node(
        CreateNodeInput(
            acm=DEFAULT_ACM,
            name=test_node_name1,
            tier=ObjectTier.DERIVATIVE,
            tags=SETTINGS.inference_tags,
            classIri=person_node_iri,
            isNso=True,
        )
    )
    yield node1
    delete_node1 = oms_crud_tool.delete_node(node1.id)
    assert delete_node1


@pytest.fixture(scope="function")
def test_node2():
    node2 = oms_crud_tool.create_node(
        CreateNodeInput(
            acm=DEFAULT_ACM,
            name=test_node_name2,
            tier=ObjectTier.DERIVATIVE,
            tags=SETTINGS.inference_tags,
            classIri=person_node_iri,
            isNso=True,
        )
    )
    yield node2
    delete_node2 = oms_crud_tool.delete_node(node_id=node2.id)
    assert delete_node2


@pytest.fixture(scope="function")
def test_relationship1(create_source, test_node1, test_node2):
    rel1 = oms_crud_tool.create_relationship(
        CreateRelationshipInput(
            name=test_relationship_name1,
            startNodeId=test_node1.id,
            endNodeId=test_node2.id,
            sourceId=create_source.id,
            confidence=Confidence.UNKNOWN,
            acm=DEFAULT_ACM,
            objectPropertyIri=work_for_relationship_iri,
        )
    )
    yield rel1
    delete_rel1 = oms_crud_tool.delete_relationship(relationship_id=rel1.id)
    assert delete_rel1


@pytest.fixture(scope="function")
def test_relationship2(create_source, test_node1, test_node2):
    rel2 = oms_crud_tool.create_relationship(
        CreateRelationshipInput(
            name=test_relationship_name2,
            startNodeId=test_node1.id,
            endNodeId=test_node2.id,
            sourceId=create_source.id,
            confidence=Confidence.UNKNOWN,
            acm=DEFAULT_ACM,
            objectPropertyIri=work_for_relationship_iri,
        )
    )
    yield rel2
    delete_rel2 = oms_crud_tool.delete_relationship(relationship_id=rel2.id)
    assert delete_rel2


@pytest.fixture(scope="function")
def test_attr1(create_source, test_node1):
    attr1 = oms_crud_tool.create_attribute(
        CreateAttributeInput(
            attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
            attributeValue=test_attribute_name1,
            attributeType=AttributeType.STRING,
            confidence=Confidence.UNKNOWN,
            sourceId=create_source.id,
            nodeId=test_node1.id,
            acm=DEFAULT_ACM,
        )
    )
    yield attr1
    delete_attr1 = oms_crud_tool.delete_attribute(attribute_id=attr1.id)
    assert delete_attr1


@pytest.fixture(scope="function")
def test_attr2(create_source, test_node1):
    attr2 = oms_crud_tool.create_attribute(
        CreateAttributeInput(
            attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
            attributeValue=test_attribute_name2,
            attributeType=AttributeType.STRING,
            confidence=Confidence.UNKNOWN,
            sourceId=create_source.id,
            nodeId=test_node1.id,
            acm=DEFAULT_ACM,
        )
    )
    yield attr2
    delete_attr2 = oms_crud_tool.delete_attribute(attribute_id=attr2.id)
    assert delete_attr2


def test_multi_crud_operations(test_node1, test_node2, test_relationship1, test_relationship2, test_attr1, test_attr2):
    assert test_node1
    assert test_node2

    assert test_relationship1
    assert test_relationship2

    assert test_attr1
    assert test_attr2


def test_node_crud(test_node1):
    # Create test
    node = test_node1
    assert node

    # Get test
    get_nodes = oms_crud_tool.get_nodes(NodeQuery(name=StringQuery(equals=test_node_name1)))
    for ind_node in get_nodes.data:
        assert ind_node.name == test_node_name1

    # Update test
    new_node_name = "new_node_name"
    update_node = oms_crud_tool.update_node(UpdateNodeInput(id=node.id, name=new_node_name))
    assert update_node
    assert update_node.name == new_node_name


def test_relationship_crud(test_node1, test_node2, test_relationship1):
    # First need to create a couple nodes that the relationship can use
    assert test_node1
    assert test_node2

    # Create test
    rel = test_relationship1
    assert rel

    # Get test
    get_rels = oms_crud_tool.get_relationships(RelationshipQuery(name=StringQuery(equals=test_relationship_name1)))
    for ind_rel in get_rels.data:
        assert ind_rel.name == test_relationship_name1

    # Update test
    new_relationship_name = "new_relationship_name"
    update_relationship = oms_crud_tool.update_relationship(
        UpdateRelationshipInput(id=rel.id, name=new_relationship_name)
    )
    assert update_relationship
    assert update_relationship.name == new_relationship_name


def test_attribute_crud(test_node1, test_attr1):
    node = test_node1
    assert node

    attribute = test_attr1
    assert attribute

    # Get test
    get_attrs = oms_crud_tool.get_attributes(AttributeQuery(attributeValue=StringQuery(equals=test_attribute_name1)))
    for ind_attr in get_attrs.data:
        assert ind_attr.attributeValue == test_attribute_name1

    # Update test
    update_attribute = oms_crud_tool.update_attribute(UpdateAttributeInput(id=attribute.id, confidence=Confidence.LOW))
    assert update_attribute
    assert update_attribute.confidence == Confidence.LOW
