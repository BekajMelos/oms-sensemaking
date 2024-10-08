from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sdk.generated.generated_graphql_client.node import NodeNode
from oms_sdk.generated.generated_graphql_client.relationship import RelationshipRelationship

from oms_sensemaking.config import SETTINGS


class NlpPublisher:
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.oms_client: Client = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )

    def publisher_pipeline(self, findings: dict):
        """Run the publisher on the findings"""
        attributes = self.format_attributes(findings)
        nodes = self.format_nodes(findings)
        relationships = self.format_relationships(findings)

        self.publish_attributes(attributes)
        self.publish_nodes(nodes)
        self.publish_relationships(relationships)

    def format_nodes(self, findings: dict) -> list[NodeNode]:
        """Format the Node objects from the findings"""
        # 1. Get the findings[ner_entities] and findings[document_entity]
        # 2. For each, format as a Node and add to list of Nodes
        pass

    def format_relationships(self, findings: dict) -> list[RelationshipRelationship]:
        """Format the Relationship objects from the findings"""
        # 1. Get the findings[ner_relationships] and findings[document_relationships]
        # 2. For each, format as a Relationship and add to list of Relationships
        # 3. Grab the uuid of each node in the relationship and add to Relationship object
        pass

    def format_attributes(self, findings: dict) -> list[AttributeAttribute]:
        """Format attribute for a Node or Relationship"""
        # TODO: decide what goes in an attribute (if anything)
        pass

    def publish_nodes(self, nodes: list[NodeNode]) -> bool:
        """Publish the Nodes to OMS"""
        # 1. for each node, publish it to OMS
        pass

    def publish_relationships(self, relationships: list[RelationshipRelationship]) -> bool:
        """Publish the relationships to OMS"""
        # 1. for each relationship, publish it to OMS
        pass

    def publish_attributes(self, attributes: list[AttributeAttribute]) -> bool:
        """Publish the attributes to oms"""
        # 1. for each attribute, publish it to OMS linked to the corresponding node
        pass

    def get_nodes(self):
        """Get existing Nodes from OMS"""
        pass

    def get_relationships(self):
        """Get existing Relationships from OMS"""
        pass

    def get_source(self):
        """Get existing Source from OMS"""
        pass

    def update_node(self):
        """Update node"""
        pass

    def update_relationship(self):
        """Update relationship"""
        pass

    def update_source(self):
        """Update source with new attributes and relationships"""
        pass

    def delete_node(self):
        """Delete existing Node from OMS"""
        pass

    def delete_relationship(self):
        """Delete existing Relationship from OMS"""
        pass

    def delete_attribute(self):
        """Delete existing attribute from OMS"""
        pass
