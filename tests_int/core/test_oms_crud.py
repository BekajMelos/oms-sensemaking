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
    UpdateSourceInput,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool

oms_crud_tool = OmsCrudTool()
person_node_iri = SETTINGS.nlp_node_iris["Person"]
work_for_relationship_iri = SETTINGS.nlp_relationship_iris["Work_For"]
test_node_name = "test_node_name"
test_attribute_name = "test_attribute_name"
test_relationship_name = "test_relationship_name"


def test_test_source_creation():
    # Test path where source already exists (it is created in conftest before testing)
    test_source = oms_crud_tool.create_test_source()
    assert test_source
    assert test_source.name == "nlp_test_source"

    # Test logic path where source does not yet exist
    new_originator_name = "new_test_nlp_originator"
    new_provider_name = "new_test_nlp_provider"
    new_source_name = "new_test_nlp_source"
    new_test_source = oms_crud_tool.create_test_source(
        test_originator_name=new_originator_name, test_provider_name=new_provider_name, test_source_name=new_source_name
    )
    assert new_test_source
    assert new_test_source.name == new_source_name

    source_id = new_test_source.id
    provider_id = new_test_source.providerId
    originator_id = oms_crud_tool.get_originator_by_name(new_originator_name).data[0].id

    # Source update
    updated_name = "updated_source_name_x"
    updated_source = oms_crud_tool.update_source(UpdateSourceInput(id=source_id, name=updated_name))
    assert updated_source.name == updated_name

    # Source get
    get_source = oms_crud_tool.get_source(source_id)
    assert get_source.name == updated_source.name

    # Delete source, provider, and originator
    assert oms_crud_tool.delete_source(source_id)
    assert oms_crud_tool.delete_provider(provider_id)
    assert oms_crud_tool.delete_originator(originator_id)


def test_multi_crud_operations(mock_source):
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
                sourceId=mock_source.id,
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
                attributeIri=SETTINGS.text_iri,
                attributeValue=test_attribute_name + f"_{i}",
                attributeType=AttributeType.STRING,
                confidence=Confidence.UNKNOWN,
                sourceId=mock_source.id,
                nodeId=nodes[0].id,
                acm=DEFAULT_ACM,
            )
        )
    attributes = oms_crud_tool.publish_attributes(attrs_to_publish)
    assert len(attributes) == 2


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


def test_relationship_crud(mock_source):
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
            sourceId=mock_source.id,
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


def test_attribute_crud(mock_source):
    # First, need to create a node that the attribute can be based on
    node = oms_crud_tool.create_node(
        CreateNodeInput(
            acm=DEFAULT_ACM,
            name=test_node_name,
            tier=ObjectTier.DERIVATIVE,
            tags=SETTINGS.nlp_tags,
            classIri=person_node_iri,
            isNso=True,
        )
    )
    assert node

    attribute = oms_crud_tool.create_attribute(
        CreateAttributeInput(
            attributeIri=SETTINGS.text_iri,
            attributeValue=test_attribute_name,
            attributeType=AttributeType.STRING,
            confidence=Confidence.UNKNOWN,
            sourceId=mock_source.id,
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
