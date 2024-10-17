from oms_sdk.generated.generated_graphql_client.input_types import (
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
)

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import OmsPublisher


class NlpOmsPublisher(OmsPublisher):
    """Formats and publishes the NLP Findings"""

    def __init__(self, source_id: str):
        self.source_id = source_id
        self.oms_crud_tool = OmsCrudTool()

    def publish(self, findings: dict):
        """
        Run the publisher on the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        attributes = self.format_attributes(findings)
        nodes = self.format_nodes(findings)
        relationships = self.format_relationships(findings)

        self.oms_crud_tool.publish_attributes(attributes)
        self.oms_crud_tool.publish_nodes(nodes)
        self.oms_crud_tool.publish_relationships(relationships)

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
