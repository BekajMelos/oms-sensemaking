from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Client, Confidence
from oms_sdk.generated.generated_graphql_client.input_types import (
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
)

from oms_sensemaking.api.schemas.oms import ObjectTier
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import OmsPublisher


class NlpOmsPublisher(OmsPublisher):
    """Formats and publishes the NLP Findings"""

    def __init__(self, source_id: str, oms_client: Client):
        super().__init__(oms_client)
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
        create_nodes_input = []

        for entity in findings["ner_entities"]:
            # Format the CreateNodeInput object
            node_input = CreateNodeInput(
                # ID????
                acm=DEFAULT_ACM,
                name=entity["value"],
                tier=ObjectTier.DERIVATIVE,
                classIri=entity["type"],
            )

            # Append the CreateNodeInput object to the list
            create_nodes_input.append(node_input)

            # TODO: Get and format attribute
            # attribute_input = []

        document_entity = findings["document_entity"]  # There's only one
        # Format the CreateNodeInput and add it to the list for the document entith
        document_node_input = CreateNodeInput(
            # ID????
            acm=DEFAULT_ACM,
            name=document_entity.text,
            tier=ObjectTier.DERIVATIVE,
            classIri=document_entity.entity_type,
        )
        create_nodes_input.append(document_node_input)

        # TODO: Get and format attribute for document node
        # attribute_input = []

        return create_nodes_input

    def format_relationships(self, findings: dict) -> list[CreateRelationshipInput]:
        """
        Format the Relationship objects from the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        # 1. Get the findings[ner_relationships] and findings[document_relationships]
        # 2. For each, format as a Relationship and add to list of Relationships
        create_relationships_input = []
        for relationship in findings["ner_relationships"]:
            relationship_input = CreateRelationshipInput(
                name=relationship["type"],
                startNodeId=relationship["entities"][0]["uuid"],
                endNodeId=relationship["entities"][1]["uuid"],
                sourceId=self.source_id,
                confidence=Confidence.UNKNOWN,
                acm=DEFAULT_ACM,
                objectPropertyIri=relationship["type"],
            )
            create_relationships_input.append(relationship_input)

            # TODO: Get and format attribute for relationship
            # attribute_input = []

        for document_relationship in findings["document_relationships"]:
            document_relationship_input = CreateRelationshipInput(
                name=document_relationship["type"],
                startNodeId=document_relationship["document_uuid"],
                endNodeId=document_relationship["entity_uuid"],
                sourceId=self.source_id,
                confidence=Confidence.UNKNOWN,
                acm=DEFAULT_ACM,
                objectPropertyIri=document_relationship["type"],
            )
            create_relationships_input.append(document_relationship_input)

            # TODO: Get and format attribute for document relationship
            # attribute_input = []

        return create_relationships_input

    def format_attributes(self, findings: dict) -> list[CreateAttributeInput]:
        """
        Format attribute for a Node or Relationship
        :param findings: The result of the NLP analysis on the body of text
        """
        # TODO: decide what goes in an attribute (if anything, could be NER label, text associated with node, etc.)
        # Link each attribute to the node that it comes from
        # TODO: Implement function
        # This may be integrated with the previous two functions
        return []
