import logging
from typing import Tuple

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

LOGGER: logging.Logger = logging.getLogger(__name__)


class NlpOmsPublisher:
    """Formats and publishes the NLP Findings"""

    def __init__(self, source_id: str, acm: dict):
        self.source_id = source_id
        self.acm = acm
        self.oms_crud_tool = OmsCrudTool()
        self.node_id_mapping: dict[str, str] = {}
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
        self.attribute_iris = {
            "URL": SETTINGS.url_iri,
            "Identifier": SETTINGS.identifier_iri,
            "Text": SETTINGS.nlp_text_iri,
        }

    def publish(self, findings: dict) -> Tuple[list[CreateNodeCreateNode], list[CreateRelationshipCreateRelationship]]:
        """
        Run the publisher on the findings
        :param findings: The result of the NLP analysis on the body of text
        """
        LOGGER.info("Publishing nodes to OMS")
        published_nodes = self.format_and_publish_nodes(findings)
        LOGGER.info("Publishing relationships to OMS")
        published_relationships = self.format_and_publish_relationships(findings)
        return published_nodes, published_relationships

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
                    acm=self.acm,
                    name=entity["value"],
                    tier=ObjectTier.DERIVATIVE,
                    tags=SETTINGS.nlp_tags,
                    classIri=self.node_iris[entity["type"]],
                    isNso=True,
                )
            )

            # Add node to list of published nodes
            published_nodes.append(published_node)

            # Update the entity ID to node ID mapping (this is used for creating relationships)
            self.node_id_mapping[entity["uuid"]] = published_node.id

            # Publish attribute containing entity's text
            self.format_and_publish_attribute(
                iri=self.attribute_iris["Text"],
                value=entity["value"],
                entity_id=entity["uuid"],
                published_node_id=published_node.id,
            )

        document_entity = findings["document_entity"]

        if document_entity:
            # Format and publish the Report node
            published_report_node = self.oms_crud_tool.create_node(
                CreateNodeInput(
                    acm=self.acm,
                    name="Report",
                    tier=ObjectTier.DERIVATIVE,
                    tags=SETTINGS.nlp_tags,
                    classIri=self.node_iris["DOCUMENT"],
                    isNso=True,
                )
            )

            # Add published document node to list of published document nodes
            published_nodes.append(published_report_node)

            # Map document entity ID to the published document Node ID
            self.node_id_mapping[document_entity["document_id"]] = published_report_node.id

            # Grab the source
            source = self.oms_crud_tool.get_source(source_id=self.source_id)

            # Publish attribute containing Report's URL
            self.format_and_publish_attribute(
                iri=self.attribute_iris["URL"],
                value=source.uri or "No URL",
                entity_id=document_entity["document_id"],
                published_node_id=published_report_node.id,
            )

            # Publish attribute containing Report's Identifier
            self.format_and_publish_attribute(
                iri=self.attribute_iris["Identifier"],
                value=source.identifier or "No Identifier",
                entity_id=document_entity["document_id"],
                published_node_id=published_report_node.id,
            )

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
            # Grab some of the relationship values
            first_ent_id = relationship["entities"][0]["uuid"]
            second_ent_id = relationship["entities"][1]["uuid"]
            relationship_classification = relationship["type"]

            # If there are no nodes for the IDs outlined by the relationship, don't create a relationship
            if first_ent_id in self.node_id_mapping and second_ent_id in self.node_id_mapping:
                # Format and publish the relationship
                published_relationship = self.oms_crud_tool.create_relationship(
                    CreateRelationshipInput(
                        name=self.relationship_iris[relationship_classification],
                        startNodeId=self.node_id_mapping[first_ent_id],
                        endNodeId=self.node_id_mapping[second_ent_id],
                        sourceId=self.source_id,
                        confidence=Confidence.UNKNOWN,
                        acm=self.acm,
                        objectPropertyIri=self.relationship_iris[relationship_classification],
                    )
                )
                published_relationships.append(published_relationship)

        for document_relationship in findings["document_relationships"]:
            # Grab some of the relationship values
            doc_id = document_relationship["document_uuid"]
            ent_id = document_relationship["entity_uuid"]
            rel_type = document_relationship["type"]

            # If there are no nodes for the IDs outlined by the relationship, don't create a relationship
            if doc_id in self.node_id_mapping and ent_id in self.node_id_mapping:
                # Format and publish the document relationship
                published_document_relationship = self.oms_crud_tool.create_relationship(
                    CreateRelationshipInput(
                        name=self.relationship_iris[rel_type],
                        startNodeId=self.node_id_mapping[doc_id],
                        endNodeId=self.node_id_mapping[ent_id],
                        sourceId=self.source_id,
                        confidence=Confidence.UNKNOWN,
                        acm=self.acm,
                        objectPropertyIri=self.relationship_iris[rel_type],
                    )
                )
                published_relationships.append(published_document_relationship)

        return published_relationships

    def format_and_publish_attribute(
        self, iri: str, value: str, entity_id: str, published_node_id: str
    ) -> CreateAttributeCreateAttribute | None:
        """
        Format and publish the published Nodes' attributes
        :param iri: IRI of the attribute to be published
        :param value: The value of the attribute to be published
        :param entity_id: The entity's unique identifier
        :param published_node_id: Node to relate to attribute
        """
        # First check if the entity has been created as a node
        if entity_id in self.node_id_mapping:
            return self.oms_crud_tool.create_attribute(
                CreateAttributeInput(
                    attributeIri=iri,
                    attributeValue=value,
                    attributeType=AttributeType.STRING,
                    confidence=Confidence.UNKNOWN,
                    sourceId=self.source_id,
                    nodeId=published_node_id,
                    acm=self.acm,
                )
            )
        else:
            return None
