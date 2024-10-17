from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributes,
    DeleteByIdInput,
    NodesNodes,
    RelationshipQuery,
    RelationshipsRelationships,
    SourceSource,
    UpdateAttributeInput,
    UpdateRelationshipInput,
    UpdateSourceInput,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeQuery,
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
    IdQuery,
    NodeQuery,
    UpdateNodeInput,
)

from oms_sensemaking.config import SETTINGS


class OmsCrudTool:
    """Tool for using OMS_SDK CRUD operations"""

    def __init__(self):
        self.oms_client: Client = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )

    ### PUBLISH/CREATE ###
    def publish_nodes(self, nodes: list[CreateNodeInput]):
        """
        Publish the Nodes to OMS
        :param nodes: a list of CreateNodeInput objects
        """
        # 1. for each node, publish it to OMS
        for node in nodes:
            self.oms_client.create_node(node)

    def publish_relationships(self, relationships: list[CreateRelationshipInput]):
        """
        Publish the relationships to OMS
        :param relationships: a list of CreateRelationshipInput objects
        """
        # 1. for each relationship, publish it to OMS
        for relationship in relationships:
            self.oms_client.create_relationship(relationship)

    def publish_attributes(self, attributes: list[CreateAttributeInput]):
        """
        Publish the attributes to oms
        :param attributes: a list of CreateAttributeInput objects
        """
        # 1. for each attribute, publish it to OMS
        for attribute in attributes:
            self.oms_client.create_attribute(attribute)

    ### GET ###
    def get_nodes(self, node_info: NodeQuery) -> NodesNodes:
        """Get existing Nodes from OMS"""
        nodes = self.oms_client.nodes(query=node_info)
        return nodes

    def get_relationships(self, relationship_info: RelationshipQuery) -> RelationshipsRelationships:
        """Get existing Relationships from OMS"""
        relationships = self.oms_client.relationships(query=relationship_info)
        return relationships

    def get_attributes(self, attribute_info: AttributeQuery) -> AttributesAttributes:
        """Get existing Attributes from OMS"""
        attributes = self.oms_client.attributes(query=attribute_info)
        return attributes

    def get_source(self, source_id: str) -> SourceSource:
        """Get existing Attributes from OMS"""
        source = self.oms_client.source(query=IdQuery(id=source_id))
        return source

    ### UPDATE ###
    def update_node(self, update_input: UpdateNodeInput):
        """Update node"""
        self.oms_client.update_node(update_input)

    def update_relationship(self, update_input: UpdateRelationshipInput):
        """Update relationship"""
        self.oms_client.update_relationship(update_input)

    def update_attribute(self, update_input: UpdateAttributeInput):
        """Update attribute"""
        self.oms_client.update_attribute(update_input)

    def update_source(self, update_input: UpdateSourceInput):
        """Update source"""
        self.update_source(update_input)

    ### DELETE ###
    def delete_node(self, node_id):
        """Update node"""
        self.oms_client.delete_node(DeleteByIdInput(id=node_id))

    def delete_relationship(self, relationship_id):
        """Update relationship"""
        self.oms_client.delete_relationship(DeleteByIdInput(id=relationship_id))

    def delete_attribute(self, attribute_id):
        """Update attribute"""
        self.oms_client.delete_attribute(DeleteByIdInput(id=attribute_id))
