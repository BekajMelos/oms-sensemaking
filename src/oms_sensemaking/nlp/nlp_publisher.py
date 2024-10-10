from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributes,
    NodesNodes,
    RelationshipQuery,
    RelationshipsRelationships,
    SourceSource,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeQuery,
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
    IdQuery,
    NodeQuery,
)

from oms_sensemaking.config import SETTINGS


class NlpOmsPublisher:
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.oms_client: Client = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )

    def publisher_pipeline(self, findings: dict):
        """
        Run the publisher on the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        attributes = self.format_attributes(findings)
        nodes = self.format_nodes(findings)
        relationships = self.format_relationships(findings)

        self.publish_attributes(attributes)
        self.publish_nodes(nodes)
        self.publish_relationships(relationships)

    def format_nodes(self, findings: dict) -> list[CreateNodeInput]:
        """
        Format the Node objects from the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        # 1. Get the findings[ner_entities] and findings[document_entity]
        # 2. For each, format as a Node and add to list of Nodes
        # TODO: Implement function
        return []

    def format_relationships(self, findings: dict) -> list[CreateRelationshipInput]:
        """
        Format the Relationship objects from the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        # 1. Get the findings[ner_relationships] and findings[document_relationships]
        # 2. For each, format as a Relationship and add to list of Relationships
        # TODO: Implement function
        return []

    def format_attributes(self, findings: dict) -> list[CreateAttributeInput]:
        """
        Format attribute for a Node or Relationship
        :param findings: The result of the NLP analysis on the body of text
        """
        # TODO: decide what goes in an attribute (if anything, could be NER label, text associated with node, etc.)
        # Link each attribute to the node that it comes from
        # TODO: Implement function
        return []

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

    def get_nodes(self) -> NodesNodes:
        """Get existing Nodes from OMS"""
        nodes = self.oms_client.nodes(
            query=NodeQuery(
                # TODO: Add query arguments
            )
        )
        return nodes

    def get_relationships(self) -> RelationshipsRelationships:
        """Get existing Relationships from OMS"""
        relationships = self.oms_client.relationships(
            query=RelationshipQuery(
                # TODO: Add query arguments
            )
        )
        return relationships

    def get_attributes(self) -> AttributesAttributes:
        """Get existing Attributes from OMS"""
        attributes = self.oms_client.attributes(
            query=AttributeQuery(
                # TODO: Add query arguments
            )
        )
        return attributes

    def get_source(self) -> SourceSource:
        """Get existing Attributes from OMS"""
        source = self.oms_client.source(
            query=IdQuery(
                # TODO: Add query arguments
            )
        )
        return source
