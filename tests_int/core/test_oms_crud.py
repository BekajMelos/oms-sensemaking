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


def test_multi_crud_operations(create_source):
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

    rels_to_publish = []
    for i in range(2):
        rels_to_publish.append(
            CreateRelationshipInput(
                name=test_relationship_name + f"_{i}",
                startNodeId=nodes[0].id,
                endNodeId=nodes[1].id,
                sourceId=create_source.id,
                confidence=Confidence.UNKNOWN,
                acm=DEFAULT_ACM,
                objectPropertyIri=work_for_relationship_iri,
            )
        )
    rels = oms_crud_tool.publish_relationships(rels_to_publish)
    assert len(rels) == 2

    attrs_to_publish = []
    for i in range(2):
        attrs_to_publish.append(
            CreateAttributeInput(
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeValue=test_attribute_name + f"_{i}",
                attributeType=AttributeType.STRING,
                confidence=Confidence.UNKNOWN,
                sourceId=create_source.id,
                nodeId=nodes[0].id,
                acm=DEFAULT_ACM,
            )
        )
    attributes = oms_crud_tool.publish_attributes(attrs_to_publish)
    assert len(attributes) == 2

    # Cleanup test data
    for attribute in attributes:
        delete_attrs = oms_crud_tool.delete_attribute(attribute_id=attribute.id)
        assert delete_attrs
    for relationship in rels:
        delete_rels = oms_crud_tool.delete_relationship(relationship_id=relationship.id)
        assert delete_rels
    for node in nodes:
        delete_nodes = oms_crud_tool.delete_node(node_id=node.id)
        assert delete_nodes


def test_node_crud():
    # Create test
    node = oms_crud_tool.create_node(
        CreateNodeInput(
            acm=DEFAULT_ACM,
            name=test_node_name,
            tier=ObjectTier.DERIVATIVE,
            tags=SETTINGS.inference_tags,
            classIri=person_node_iri,
            isNso=True,
        )
    )
    assert node

    # Get test
    get_nodes = oms_crud_tool.get_nodes(NodeQuery(name=StringQuery(equals=test_node_name)))
    for ind_node in get_nodes.data:
        assert ind_node.name == test_node_name

    # Update test
    new_node_name = "new_node_name"
    update_node = oms_crud_tool.update_node(UpdateNodeInput(id=node.id, name=new_node_name))
    assert update_node
    assert update_node.name == new_node_name

    # Delete test
    delete_node = oms_crud_tool.delete_node(node_id=node.id)
    assert delete_node


def test_relationship_crud(create_source):
    # First need to create a couple nodes that the relationship can use
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

    # Create test
    rel = oms_crud_tool.create_relationship(
        CreateRelationshipInput(
            name=work_for_relationship_iri,
            startNodeId=nodes[0].id,
            endNodeId=nodes[1].id,
            sourceId=create_source.id,
            confidence=Confidence.UNKNOWN,
            acm=DEFAULT_ACM,
            objectPropertyIri=work_for_relationship_iri,
        )
    )
    assert rel

    # Get test
    get_rels = oms_crud_tool.get_relationships(RelationshipQuery(name=StringQuery(equals=test_relationship_name)))
    for ind_rel in get_rels.data:
        assert ind_rel.name == test_relationship_name

    # Update test
    new_relationship_name = "new_relationship_name"
    update_relationship = oms_crud_tool.update_relationship(
        UpdateRelationshipInput(id=rel.id, name=new_relationship_name)
    )
    assert update_relationship
    assert update_relationship.name == new_relationship_name

    # Delete test
    delete_relationship = oms_crud_tool.delete_relationship(relationship_id=rel.id)
    assert delete_relationship

    # Cleanup test data
    for node in nodes:
        delete_nodes = oms_crud_tool.delete_node(node_id=node.id)
        assert delete_nodes


def test_attribute_crud(create_source):
    node = oms_crud_tool.create_node(
        CreateNodeInput(
            acm=DEFAULT_ACM,
            name=test_node_name,
            tier=ObjectTier.DERIVATIVE,
            tags=SETTINGS.inference_tags,
            classIri=person_node_iri,
            isNso=True,
        )
    )
    assert node

    attribute = oms_crud_tool.create_attribute(
        CreateAttributeInput(
            attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
            attributeValue=test_attribute_name,
            attributeType=AttributeType.STRING,
            confidence=Confidence.UNKNOWN,
            sourceId=create_source.id,
            nodeId=node.id,
            acm=DEFAULT_ACM,
        )
    )
    assert attribute

    # Get test
    get_attrs = oms_crud_tool.get_attributes(AttributeQuery(attributeValue=StringQuery(equals=test_attribute_name)))
    for ind_attr in get_attrs.data:
        assert ind_attr.attributeValue == test_attribute_name

    # Update test
    update_attribute = oms_crud_tool.update_attribute(UpdateAttributeInput(id=attribute.id, confidence=Confidence.LOW))
    assert update_attribute
    assert update_attribute.confidence == Confidence.LOW

    # Delete test
    delete_attribute = oms_crud_tool.delete_attribute(attribute_id=attribute.id)
    assert delete_attribute

    # Cleanup test data
    delete_nodes = oms_crud_tool.delete_node(node_id=node.id)
    assert delete_nodes
