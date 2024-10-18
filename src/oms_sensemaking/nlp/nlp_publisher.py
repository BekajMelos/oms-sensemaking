from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
    Confidence,
    CreateAttributeCreateAttribute,
    CreateNodeCreateNode,
    CreateRelationshipCreateRelationship,
)
from oms_sdk.generated.generated_graphql_client.input_types import (
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
)

from oms_sensemaking.api.schemas.oms import ObjectTier
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool


class NlpOmsPublisher:
    """Formats and publishes the NLP Findings"""

    def __init__(self, source_id: str):
        self.source_id = source_id
        self.oms_crud_tool = OmsCrudTool()
        self.node_id_mapping = {}
        self.node_iris = {
            "PEOPLE": SETTINGS.nlp_person_iri,
            "ORGANIZATION": SETTINGS.nlp_organization_iri,
            "LOCATION": SETTINGS.nlp_location_iri,
            "DOCUMENT": SETTINGS.nlp_document_iri,
            "DATE": SETTINGS.nlp_date_iri,
        }
        self.relationship_iris = {
            "Work_For": SETTINGS.nlp_work_for_iri,
            "Live_In": SETTINGS.nlp_live_in_iri,
            "OrgBased_In": SETTINGS.nlp_org_based_in_iri,
            "Located_In": SETTINGS.nlp_located_in_iri,
            "Document_Contains_Entity": SETTINGS.nlp_document_contains_entity_iri,
        }

    def publish(self, findings: dict):
        """
        Run the publisher on the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        self.format_and_publish_nodes(findings)
        self.format_and_publish_relationships(findings)

    def format_and_publish_nodes(self, findings: dict) -> list[CreateNodeCreateNode]:
        """
        Format the Node objects from the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        # 1. Get the findings[ner_entities] and findings[document_entity]
        # 2. For each, format as a Node and publish
        published_nodes = []

        for entity in findings["ner_entities"]:
            # Format and publish node
            published_node = self.oms_crud_tool.create_node(
                CreateNodeInput(
                    acm=DEFAULT_ACM,
                    name=entity["value"],
                    tier=ObjectTier.DERIVATIVE,
                    tags=[SETTINGS.node_tag],
                    classIri=self.node_iris[entity["type"]],
                    isNso=True,
                )
            )

            # Add node to list of published nodes
            published_nodes.append(published_node)

            # Update the entity ID to node ID mapping (this is used for creating relationships)
            self.node_id_mapping[entity["uuid"]] = published_node.id

            # Publish attribute containing entity's text
            self.format_and_publish_attribute(entity, published_node)

        document_entity = findings["document_entity"]

        # Format and publish the document node
        published_document_node = self.oms_crud_tool.create_node(
            CreateNodeInput(
                acm=DEFAULT_ACM,
                name="Document Entity",
                tier=ObjectTier.DERIVATIVE,
                tags=[SETTINGS.node_tag],
                classIri=self.node_iris["DOCUMENT"],
                isNso=True,
            )
        )

        # Add published document node to list of published document nodes
        published_nodes.append(published_document_node)

        # Map document entity ID to the published document Node ID
        self.node_id_mapping[document_entity["document_id"]] = published_document_node.id

        # Publish attribute containing document's text
        self.format_and_publish_attribute(document_entity, published_document_node)

        return published_nodes

    def format_and_publish_relationships(self, findings: dict) -> list[CreateRelationshipCreateRelationship]:
        """
        Format and publish the Relationship objects from the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        # 1. Get the findings[ner_relationships] and findings[document_relationships]
        # 2. For each, format as a Relationship and publish
        published_relationships = []
        for relationship in findings["ner_relationships"]:
            # Format and publish the relationship
            self.oms_crud_tool.create_relationship(
                CreateRelationshipInput(
                    name=self.relationship_iris[relationship["type"]],
                    startNodeId=self.node_id_mapping[relationship["entities"][0]["uuid"]],
                    endNodeId=self.node_id_mapping[relationship["entities"][1]["uuid"]],
                    sourceId=self.source_id,
                    confidence=Confidence.UNKNOWN,
                    acm=DEFAULT_ACM,
                    objectPropertyIri=self.relationship_iris[relationship["type"]],
                )
            )

        for document_relationship in findings["document_relationships"]:
            # Format and publish the document relationship
            self.oms_crud_tool.create_relationship(
                CreateRelationshipInput(
                    name=self.relationship_iris[document_relationship["type"]],
                    startNodeId=self.node_id_mapping[document_relationship["document_uuid"]],
                    endNodeId=self.node_id_mapping[document_relationship["entity_uuid"]],
                    sourceId=self.source_id,
                    confidence=Confidence.UNKNOWN,
                    acm=DEFAULT_ACM,
                    objectPropertyIri=self.relationship_iris[document_relationship["type"]],
                )
            )

        return published_relationships

    def format_and_publish_attribute(
        self, entity: dict, published_node: CreateNodeCreateNode
    ) -> CreateAttributeCreateAttribute:
        """
        Format and publish the published Nodes' attributes
        :param entity: Entity to extract attribute from
        :param published_node: Node to relate to attribute
        """
        return self.oms_crud_tool.create_attribute(
            CreateAttributeInput(
                attributeIri=SETTINGS.nlp_attribute_iri,
                attributeValue=entity["value"],
                attributeType=AttributeType.STRING,
                confidence=Confidence.UNKNOWN,
                sourceId=self.source_id,
                nodeId=published_node.id,
                acm=DEFAULT_ACM,
            )
        )
