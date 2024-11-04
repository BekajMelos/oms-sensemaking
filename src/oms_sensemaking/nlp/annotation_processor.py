"""Annotation Processor."""

import logging
import re
from uuid import uuid4

from oms_sensemaking.nlp.models.document_as_entity import DocumentAsEntity
from oms_sensemaking.nlp.models.document_has_relation import DocumentHasRelation
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.models.submission_data import SubmissionData

LOGGER: logging.Logger = logging.getLogger(__name__)


class AnnotationProcessor:
    """
    A utility class for extracting entities and relationships from annotated documents.

    This takes the annotated document, gets entities and relationships, and returns them all.
    It also creates relationships between a document and each of the entities found within it.
    """

    def __init__(self):
        self.sentence_pattern = re.compile(r"Sentence #\d+.*?(?=\nSentence #|$)", re.DOTALL)
        self.token_pattern = re.compile(
            r"\[Text=(?P<text>[^]]+) CharacterOffsetBegin=(?P<char_offset_begin>\d+) "
            r"CharacterOffsetEnd=(?P<char_offset_end>\d+) PartOfSpeech=(?P<pos>[^]]+) "
            r"Lemma=(?P<lemma>[^]]+) NamedEntityTag=(?P<ner>[^]]+)]"
        )
        self.entity_pattern = re.compile(
            r"EntityMention \[type=(?P<type>\w+), objectId=(?P<objectId>EntityMention-\d+), hstart=(?P<hstart>\d+), "
            r"hend=(?P<hend>\d+), estart=(?P<estart>\d+), eend=(?P<eend>\d+), "
            r'headPosition=(?P<headPosition>\d+), value="(?P<value>[^"]+)", corefID=(?P<corefID>-?\d+)]'
        )
        self.relation_pattern = re.compile(
            r"RelationMention \[type=(?P<type>\w+), start=(?P<start>\d+), end=(?P<end>\d+), \{(?P<relations>[^}]+)}\n"
            r"(?P<entities>(?:\s+EntityMention \[type=\w+, objectId=EntityMention-\d+, "
            r"hstart=\d+, hend=\d+, estart=\d+, "
            r'eend=\d+, headPosition=\d+, value="[^"]+", corefID=-?\d+]\n)+)]'
        )
        self.uuid_entity_map = {}

    def extract_info(self, data: SubmissionData, annotation: str) -> EntitiesAndRelationships:
        """
        Extract the entities and relationships the given CoreNLP annotation.

        :param data: The document data.
        :param annotation: The annotation.
        :return: An object representing the entities and relationships.
        """
        LOGGER.info("Gathering entities and relationships from the annotation")

        sentences = self.find_sentences(annotation)

        # For each sentence in the annotation, identify the tokens, entities, and relationships in it
        entities, relationships = [], []
        for sentence in sentences:
            tokens = self.find_tokens(sentence)  # Get tokens just for this sentence
            entities += self.find_entities(sentence, tokens)  # Get entities from sentence, add to list
            relationships += self.find_relationships(sentence, tokens)  # Get relations from sentence, add to list
        entities_and_relationships = self.relate_to_document(data, entities, relationships)

        LOGGER.debug(f"Findings: {entities_and_relationships}")
        return entities_and_relationships

    def find_sentences(self, annotation: str) -> list[str]:
        """
        Find all instances of sentences in the corenlp response, and return a list of them
        :param annotation: CoreNLP annotation response
        """
        sentences = self.sentence_pattern.findall(annotation)
        return sentences

    def find_tokens(self, sentence: str) -> list[dict[str, str]]:
        """
        Extract the tokens from the given Annotation
        :param sentence: A sentence of the CoreNLP annotation response
        """
        token_matches = self.token_pattern.finditer(sentence)
        tokens = []
        for match in token_matches:
            token = match.groupdict()
            tokens.append(token)
        return tokens

    def find_entities(self, sentence: str, tokens: list[dict[str, str]]) -> list:
        """
        Grab the entities from the annotation.
        :param sentence: A sentence of the CoreNLP annotation response
        :param tokens: The tokens in the sentence
        """
        LOGGER.debug("Finding entities in the annotation")
        entities = []

        # Apply regex to the annotation to find the entities
        matches = self.entity_pattern.finditer(sentence)
        for match in matches:
            # Match entity to the corresponding token, and get NER tag from token
            entity_token_index = int(match.group("estart"))
            corresponding_token = tokens[entity_token_index]
            entity_type = corresponding_token["ner"]

            # Only build entity if not seen before, leave out duplicates
            entity_obj_id = match.group("objectId")
            if entity_obj_id not in self.uuid_entity_map:
                # Create unique id for each entity, and add to map
                entity_uuid = str(uuid4())
                self.uuid_entity_map[entity_obj_id] = entity_uuid

                # Build the entity if it is typed
                is_object_entity = "0" not in entity_type
                if is_object_entity:
                    # TODO: check for prefix of multi-token entities
                    multi_beginning_entity = entity_type[:2] == "B-"
                    multi_intermediate_entity = entity_type[:2] == "I-"
                    multi_end_entity = entity_type[:2] == "E-"
                    multi_token_entity = multi_beginning_entity or multi_intermediate_entity or multi_end_entity
                    if multi_token_entity:
                        entity_type = entity_type[2:]

                    entity = {
                        "type": entity_type,
                        "objectId": entity_obj_id,
                        "uuid": entity_uuid,
                        "hstart": match.group("hstart"),
                        "hend": match.group("hend"),
                        "estart": match.group("estart"),
                        "eend": match.group("eend"),
                        "headPosition": match.group("headPosition"),
                        "value": match.group("value"),
                        "corefID": match.group("corefID"),
                    }

                    entities.append(entity)

        LOGGER.debug(f"Annotation entities: {entities}")
        return entities

    def find_relationships(self, sentence: str, tokens: list[dict[str, str]]) -> list:
        """
        Grab the relationships from the annotation.
        :param sentence: A sentence of the CoreNLP annotation response
        :param tokens: The tokens in the sentence
        """
        LOGGER.debug("Finding relationships in the annotation")
        relationships = []

        # Find relations from the text using the regex pattern
        relation_matches = self.relation_pattern.finditer(sentence)

        relation_count = 1  # For keeping track of the relation object id
        for match in relation_matches:
            # Build the relation
            relation = {
                "type": match.group("type"),
                "objectId": f"RelationMention-{relation_count}",
                "uuid": str(uuid4()),
                "start": match.group("start"),
                "end": match.group("end"),
                "relations": match.group("relations").split("; "),
                "entities": [],
            }
            relation_count += 1  # Increment the relation object id

            # Find nested entity mentions within each relation mention
            nested_entities = self.entity_pattern.finditer(match.group("entities"))

            # Build each entity that is found in the relation
            for entity_match in nested_entities:
                # Match entity to the corresponding token, and get NER tag from token
                entity_token_index = int(entity_match.group("estart"))
                corresponding_token = tokens[entity_token_index]
                entity_type = corresponding_token["ner"]

                # Get the entity's uuid using its object id
                entity_object_id = entity_match.group("objectId")  # Get the object id from the regex
                entity_uuid = self.uuid_entity_map[entity_object_id]

                # TODO: check for prefix of multi-token entities
                multi_beginning_entity = entity_type[:2] == "B-"
                multi_intermediate_entity = entity_type[:2] == "I-"
                multi_end_entity = entity_type[:2] == "E-"
                multi_token_entity = multi_beginning_entity or multi_intermediate_entity or multi_end_entity
                if multi_token_entity:
                    entity_type = entity_type[2:]

                # Build the entity
                entity = {
                    "type": entity_type,
                    "objectId": entity_object_id,
                    "uuid": entity_uuid,
                    "hstart": entity_match.group("hstart"),
                    "hend": entity_match.group("hend"),
                    "estart": entity_match.group("estart"),
                    "eend": entity_match.group("eend"),
                    "headPosition": entity_match.group("headPosition"),
                    "value": entity_match.group("value"),
                    "corefID": entity_match.group("corefID"),
                }
                # Add the entity to the relation's entities
                relation["entities"].append(entity)

            # Add the relation to the list of relations IF it has a type AND its entities both have types
            is_relationship = relation["type"] != "_NR"
            typed_entities = "0" not in relation["entities"][0]["type"] and "0" not in relation["entities"][1]["type"]
            if is_relationship and typed_entities:
                relationships.append(relation)
            elif not is_relationship:
                LOGGER.warning(f"Typeless relationship found: {relation}")
            elif not typed_entities:
                LOGGER.warning(f"One or more typeless entity found: {relation["entities"]}")

        LOGGER.debug(f"Annotation relationships: {relationships}")
        return relationships

    def relate_to_document(self, data: SubmissionData, entities: list, relationships: list) -> EntitiesAndRelationships:
        """
        Convert document into a node and create a relationship to each entity found in the document.

        :param data: The document data.
        :param entities: A list of entities.
        :param relationships:
        :return:
        """
        LOGGER.debug("Recording relationship between document/report and found entities.")

        document_relationships = []

        # 1. Create entity for document
        document_entity = DocumentAsEntity(document_id=data.document_id, value=data.text)
        doc_rel_index = 1

        # 2. Relate each entity in the document to the document's entity
        for entity in entities:
            # Loop through all the entities and creates a DocumentHasRelationship for each of them
            doc_rel_obj_id = "DocumentRelation-" + str(doc_rel_index)
            document_relationship = DocumentHasRelation(
                doc_obj_id=doc_rel_obj_id,
                document_uuid=data.document_id,
                entity_obj_id=entity["objectId"],
                entity_uuid=entity["uuid"],
            )
            document_relationships.append(document_relationship)
            doc_rel_index += 1

        LOGGER.debug(f"Document/report relationships: {document_relationships}")

        return EntitiesAndRelationships(
            ner_entities=entities,
            ner_relationships=relationships,
            document_entity=document_entity,
            document_relationships=document_relationships,
        )
