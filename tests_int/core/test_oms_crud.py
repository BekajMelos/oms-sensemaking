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
test_node_name = "test_node_name"
test_attribute_name = "test_attribute_name"
test_relationship_name = "test_relationship_name"


@pytest.fixture(scope="function")
def test_nodes():
    nodes_to_publish = []
    for i in range(2):
        nodes_to_publish.append(
            CreateNodeInput(
                acm=DEFAULT_ACM,
                name=test_node_name + f"_{i}",
                tier=ObjectTier.DERIVATIVE,
                tags=SETTINGS.inference_tags,
                classIri=person_node_iri,
                isNso=True,
            )
        )
    nodes = oms_crud_tool.publish_nodes(nodes_to_publish)
    assert len(nodes) == 2
    yield nodes
    del_node1 = oms_crud_tool.delete_node(node_id=nodes[0].id)
    del_node2 = oms_crud_tool.delete_node(node_id=nodes[1].id)
    assert del_node1, del_node2


@pytest.fixture(scope="function")
def test_relationships(create_source, test_nodes):
    rels_to_publish = []
    for i in range(2):
        rels_to_publish.append(
            CreateRelationshipInput(
                name=test_relationship_name + f"_{i}",
                startNodeId=test_nodes[0].id,
                endNodeId=test_nodes[1].id,
                sourceId=create_source.id,
                confidence=Confidence.UNKNOWN,
                acm=DEFAULT_ACM,
                objectPropertyIri=work_for_relationship_iri,
            )
        )
    rels = oms_crud_tool.publish_relationships(rels_to_publish)
    assert len(rels) == 2
    yield rels
    del_rel1 = oms_crud_tool.delete_relationship(relationship_id=rels[0].id)
    del_rel2 = oms_crud_tool.delete_relationship(relationship_id=rels[1].id)
    assert del_rel1, del_rel2


@pytest.fixture(scope="function")
def test_attrs(create_source, test_nodes):
    attrs_to_publish = []
    for i in range(2):
        attrs_to_publish.append(
            CreateAttributeInput(
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeValue=test_attribute_name + f"_{i}",
                attributeType=AttributeType.STRING,
                confidence=Confidence.UNKNOWN,
                sourceId=create_source.id,
                nodeId=test_nodes[0].id,
                acm=DEFAULT_ACM,
            )
        )
    attributes = oms_crud_tool.publish_attributes(attrs_to_publish)
    assert len(attributes) == 2
    yield attributes
    del_attr1 = oms_crud_tool.delete_attribute(attribute_id=attributes[0].id)
    del_attr2 = oms_crud_tool.delete_attribute(attribute_id=attributes[1].id)
    assert del_attr1, del_attr2


def test_node_crud(test_nodes):
    # Create test
    node = test_nodes[0]
    assert node

    # Get test
    get_nodes = oms_crud_tool.get_nodes(NodeQuery(name=StringQuery(equals=test_node_name + "_1")))
    for ind_node in get_nodes.data:
        assert ind_node.name == test_node_name + "_1"

    # Update test
    new_node_name = "new_node_name"
    update_node = oms_crud_tool.update_node(UpdateNodeInput(id=node.id, name=new_node_name))
    assert update_node
    assert update_node.name == new_node_name


def test_relationship_crud(test_relationships):
    # Set test rel
    rel = test_relationships[0]

    # Get test
    get_rels = oms_crud_tool.get_relationships(
        RelationshipQuery(name=StringQuery(equals=test_relationship_name + "_1"))
    )
    for ind_rel in get_rels.data:
        assert ind_rel.name == test_relationship_name + "_1"

    # Update test
    new_relationship_name = "new_relationship_name"
    update_relationship = oms_crud_tool.update_relationship(
        UpdateRelationshipInput(id=rel.id, name=new_relationship_name)
    )
    assert update_relationship
    assert update_relationship.name == new_relationship_name


def test_attribute_crud(test_attrs):
    attribute = test_attrs[0]

    # Get test
    get_attrs = oms_crud_tool.get_attributes(
        AttributeQuery(attributeValue=StringQuery(equals=test_attribute_name + "_1"))
    )
    for ind_attr in get_attrs.data:
        assert ind_attr.attributeValue == test_attribute_name + "_1"

    # Update test
    update_attribute = oms_crud_tool.update_attribute(UpdateAttributeInput(id=attribute.id, confidence=Confidence.LOW))
    assert update_attribute
    assert update_attribute.confidence == Confidence.LOW
