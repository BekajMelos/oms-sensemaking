import logging

from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
    Confidence,
)
from oms_sdk.generated.generated_graphql_client.input_types import (
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
)

from oms_sensemaking.api.schemas.oms import ObjectTier
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import OmsPublisher

LOGGER: logging.Logger = logging.getLogger(__name__)

REPORT_NODE_NAME = "Report"
NO_URL_VALUE = "No URL"
NO_IDENTIFIER_VALUE = "No Identifier"
UNPUBLISHED = "UNPUBLISHED"


class NlpOmsPublisher(OmsPublisher):
    """Formats and publishes the NLP Findings"""

    def __init__(self, source_id: str, acm: dict, oms_crud_tool: OmsCrudTool):
        super().__init__(oms_crud_tool)
        self.source_id = source_id
        self.acm = acm

    def format_nodes(self, data: str, results: dict) -> list[CreateNodeInput]:
        """ """
        formatted_nodes = []
        for entity in results["ner_entities"]:
            self.node_uuid_list.append(entity["uuid"])
            entity_type = entity["type"]
            entity_iri = SETTINGS.nlp_node_iris.get(entity_type, SETTINGS.nlp_default_node_iri)

            formatted_nodes.append(
                CreateNodeInput(
                    acm=self.acm,
                    name=entity["value"],
                    tier=ObjectTier.DERIVATIVE,
                    tags=SETTINGS.nlp_tags,
                    classIri=entity_iri,
                    isNso=True,
                )
            )

        document_entity = results["document_entity"]

        if document_entity:
            self.node_uuid_list.append(document_entity["document_id"])
            formatted_nodes.append(
                CreateNodeInput(
                    acm=self.acm,
                    name=REPORT_NODE_NAME,
                    tier=ObjectTier.DERIVATIVE,
                    tags=SETTINGS.nlp_tags,
                    classIri=SETTINGS.nlp_node_iris["Document"],
                    isNso=True,
                )
            )

        return formatted_nodes

    def format_relationships(self, data: str, results: dict) -> list[CreateRelationshipInput]:
        """ """
        formatted_relationships = []
        for relationship in results["ner_relationships"]:
            # Grab some of the relationship values
            first_ent_id = relationship["entities"][0]["uuid"]
            second_ent_id = relationship["entities"][1]["uuid"]
            relationship_type = relationship["type"]
            relationship_iri = (
                SETTINGS.nlp_relationship_iris.get(relationship_type, SETTINGS.nlp_default_relationship_iri)
            )

            if first_ent_id in self.node_id_mapping and second_ent_id in self.node_id_mapping:
                # Format and publish the relationship
                formatted_relationships.append(
                    CreateRelationshipInput(
                        name=relationship_iri,
                        startNodeId=self.node_id_mapping[first_ent_id],
                        endNodeId=self.node_id_mapping[second_ent_id],
                        sourceId=self.source_id,
                        confidence=Confidence.UNKNOWN,
                        acm=self.acm,
                        objectPropertyIri=relationship_iri,
                        tags=SETTINGS.nlp_tags,
                    )
                )

        for document_relationship in results["document_relationships"]:
            # Grab some of the relationship values
            doc_id = document_relationship["document_uuid"]
            ent_id = document_relationship["entity_uuid"]
            rel_type = document_relationship["type"]

            # If there are no nodes for the IDs outlined by the relationship, don't create a relationship
            if doc_id in self.node_id_mapping and ent_id in self.node_id_mapping:
                # Format and publish the document relationship
                formatted_relationships.append(
                    CreateRelationshipInput(
                        name=SETTINGS.nlp_relationship_iris[rel_type],
                        startNodeId=self.node_id_mapping[doc_id],
                        endNodeId=self.node_id_mapping[ent_id],
                        sourceId=self.source_id,
                        confidence=Confidence.UNKNOWN,
                        acm=self.acm,
                        objectPropertyIri=SETTINGS.nlp_relationship_iris[rel_type],
                        tags=SETTINGS.nlp_tags,
                    )
                )

        return formatted_relationships

    def format_attributes(self, data: str, results: dict) -> list[CreateAttributeInput]:
        formatted_attributes = []

        # Construct attribute inputs for the entities
        for entity in results["ner_entities"]:
            entity_id = entity["uuid"]
            if entity_id in self.node_id_mapping:
                formatted_attributes.append(
                    CreateAttributeInput(
                        attributeIri=SETTINGS.text_iri,
                        attributeValue=entity["value"],
                        attributeType=AttributeType.STRING,
                        confidence=Confidence.UNKNOWN,
                        sourceId=self.source_id,
                        nodeId=self.node_id_mapping[entity["uuid"]],
                        acm=self.acm,
                        tags=SETTINGS.nlp_tags,
                    )
                )

        document_entity = results["document_entity"]

        if document_entity:
            document_entity_id = document_entity["document_id"]
            if document_entity_id in self.node_id_mapping:
                # Construct attribute input containing Report's URL
                source = self.oms_crud_tool.get_source(source_id=self.source_id)
                url_value = source.uri or NO_URL_VALUE
                formatted_attributes.append(
                    CreateAttributeInput(
                        attributeIri=SETTINGS.url_iri,
                        attributeValue=url_value,
                        attributeType=AttributeType.STRING,
                        confidence=Confidence.UNKNOWN,
                        sourceId=self.source_id,
                        nodeId=self.node_id_mapping[document_entity_id],
                        acm=self.acm,
                        tags=SETTINGS.nlp_tags,
                    )
                )

                # Construct attribute input containing Report's Identifier
                identifier_value = source.identifier or NO_IDENTIFIER_VALUE
                formatted_attributes.append(
                    CreateAttributeInput(
                        attributeIri=SETTINGS.identifier_iri,
                        attributeValue=identifier_value,
                        attributeType=AttributeType.STRING,
                        confidence=Confidence.UNKNOWN,
                        sourceId=self.source_id,
                        nodeId=self.node_id_mapping[document_entity_id],
                        acm=self.acm,
                        tags=SETTINGS.nlp_tags,
                    )
                )

        return formatted_attributes
