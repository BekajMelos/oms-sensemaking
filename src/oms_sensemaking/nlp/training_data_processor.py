import argparse
import json
import logging

from collections_extended import RangeMap

from oms_sensemaking.nlp.corenlp_service import CoreNlpService
from oms_sensemaking.nlp.models.doccano_entity import DoccanoEntity
from oms_sensemaking.nlp.models.doccano_relation import DoccanoRelation
from oms_sensemaking.nlp.models.doccano_result import DoccanoResult
from oms_sensemaking.nlp.models.processed_relation import ProcessedRelation
from oms_sensemaking.nlp.models.processed_result import ProcessedResult
from oms_sensemaking.nlp.models.token_reference import TokenReference

logger = logging.getLogger(__name__)


class TrainingDataProcessor:
    def __init__(self, annotated_filepath: str, ner_save_filepath: str, relation_save_filepath: str):
        self.annotated_filepath = annotated_filepath
        self.ner_save_filepath = ner_save_filepath
        self.relation_save_filepath = relation_save_filepath
        self.properties = {"annotators": "tokenize, pos, lemma, depparse"}

    def run_pipeline(self):
        """The entire pipeline of functions needed to convert .jsonl to proper .tsv format for CoreNLP model training"""
        doccano_result = self.load_jsonl_file()
        processed_doccano_result = self.process_doccano_result(doccano_result)
        self.write_ner_result(processed_doccano_result, self.ner_save_filepath)
        self.write_relation_result(processed_doccano_result, self.relation_save_filepath)

    def load_jsonl_file(self) -> DoccanoResult:
        """Opens the .jsonl Doccano-annotated file and formats the data as a DoccanoResult"""
        with open(self.annotated_filepath, "r") as file:
            file_contents = json.loads(file.read())
        return DoccanoResult(
            file_contents["id"],
            file_contents["text"],
            {DoccanoEntity(entity) for entity in file_contents["entities"]},
            {DoccanoRelation(relation) for relation in file_contents["relations"]},
            file_contents["Comments"],
        )

    def process_doccano_result(self, doccano_result: DoccanoResult) -> ProcessedResult:
        """
        This function builds the ProcessedResult data type and has three parts:
        1. Using the CoreNLP client to get tokens from the text
        2. Going through the DoccanoResult entities and mapping them to tokens
        3. Going through the DoccanoResult relations and mapping Relations between tokens
        """

        # Tokenize the entities and relations
        text = doccano_result.text
        processed_result = ProcessedResult(doccano_result.id)

        # [Part 1]
        doc_token_range_map = self.tokenize_text(text)
        processed_result.doc_token_map = doc_token_range_map

        # [Part 2]
        # Build the map of entity ID to token
        entity_token_map = self.map_entities_to_tokens(doccano_result, doc_token_range_map)
        processed_result.entity_token_ref = entity_token_map

        # [Part 3]
        # Go through relations and grab necessary info to add to processed result
        processed_relation_set = self.link_relations(doccano_result, entity_token_map)
        processed_result.processed_relation_set = processed_relation_set

        return processed_result

    def tokenize_text(self, text: str) -> RangeMap:
        """Using the CoreNLP client to get tokens from the text"""

        if not text:
            text = ""
        # Go through text, annotate with CoreNLP client, and get sentences
        # The client is used here only for annotation purposes, no NER or relation extraction yet
        corenlp_client = CoreNlpService(props=self.properties, text=text)
        annotation = corenlp_client.annotate_document(text)
        sentences = annotation.sentence  # grab the sentences from the annotation

        # Loop through sentences of the annotation and grab tokens for doccano token map
        global_token_index = 0
        doc_token_range_map = RangeMap()  # Imported data type, maps ranges of char offsets to TokenReferences
        for sentence in sentences:
            for token in sentence.token:
                # Building the TokenReference with the token parts taken from the sentence
                start_offset = token.beginChar
                end_offset = token.endChar
                pos_tag = token.pos
                token_reference = TokenReference(
                    token.originalText, global_token_index, start_offset, end_offset, "0", pos_tag
                )
                global_token_index += 1

                # add new token to range map
                doc_token_range_map.set(token_reference, start_offset, end_offset)

        return doc_token_range_map

    def map_entities_to_tokens(
        self, doccano_result: DoccanoResult, doc_token_range_map: RangeMap
    ) -> dict[int, list[TokenReference]]:
        """Going through the DoccanoResult entities and mapping them to tokens"""
        entity_token_map = {}
        for doccano_entity in doccano_result.entities:
            # Get list of tokens in the offset range
            # From Java implementation: '-2' was required on the end to prevent the inclusion of trailing punctuation
            tokens_in_range = doc_token_range_map.get_range(doccano_entity.start_offset, doccano_entity.end_offset - 2)
            token_list = [tokens_in_range[key] for key in tokens_in_range]  # Token list derived from RangeMap

            # When there are multiple entities/tokens per label, need the result of the following:
            token_count = len(token_list)
            for i in range(token_count):
                current_token = token_list[i]
                current_label = doccano_entity.label

                # Setting the label prefix based on what number token of a multi-token label the current token is
                if i == 0:
                    label_prefix = "B-"
                elif i == token_count - 1:
                    label_prefix = "E-"
                else:
                    label_prefix = "I-"

                # Updating the label for the entity ONLY if there are multiple tokens for this label
                updated_label = current_label if token_count == 1 else label_prefix + current_label

                # Adding the token with the updated label back to the RangeMap
                current_token.label = updated_label
                doc_token_range_map.delete(current_token.start_offset, current_token.end_offset)
                doc_token_range_map.set(current_token, current_token.start_offset, current_token.end_offset)

                # Update the dict of tokens by id
                entity_token_map[doccano_entity.id] = current_token

        return entity_token_map

    def link_relations(
        self, doccano_result: DoccanoResult, entity_token_map: dict[int, list[TokenReference]]
    ) -> set[ProcessedRelation]:
        """Going through the DoccanoResult relations and mapping Relations between tokens"""
        processed_relation_set = set({})
        for doccano_relation in doccano_result.relations:
            # Get each of the features of a doccano relation
            from_id = doccano_relation.from_id
            to_id = doccano_relation.to_id

            # get the entities that are part of the relation from the entity_token_map
            from_token_index = entity_token_map[from_id].index
            to_token_index = entity_token_map[to_id].index

            # build the processed relation and add to the set of processed relations
            processed_relation = ProcessedRelation(from_token_index, to_token_index, doccano_relation.type)
            processed_relation_set.add(processed_relation)
        return processed_relation_set

    def write_ner_result(self, processed_result: ProcessedResult, ner_filepath: str):
        """Formats and saves the NER info from ProcessedResult to the specified NER .tsv file"""
        try:
            with open(ner_filepath, "w") as file:
                token_refs = processed_result.doc_token_map

                # Writing the NER label information for each entity to the file
                for ref in token_refs.values():
                    # Formatting the data to write to the file and then writing
                    write_string = "%s\t%s\n" % (ref.token, ref.label)
                    file.write(write_string)

        except OSError:
            logger.error("Unable to open or create NER .tsv file.")

    def write_relation_result(self, processed_result: ProcessedResult, relation_filepath: str):
        """Formats and saves the Relation info from ProcessedResult to the specified Relation .tsv file"""
        try:
            with open(relation_filepath, "w") as file:
                token_refs = processed_result.doc_token_map

                # writing the relation details for each token
                for ref in token_refs.values():
                    # Formatting the data to write to the file and then writing
                    write_string = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                        str(processed_result.doc_id),
                        ref.label,
                        str(ref.index),
                        "0",
                        ref.pos_tag,
                        ref.token,
                        "0",
                        "0",
                        "0",
                    )
                    file.write(write_string)

                file.write("\n")  # Adding an extra line between the above and below parts

                # writing summary of existing relations at the bottom of the file
                for processed_relation in processed_result.processed_relation_set:
                    write_string = "%s\t%s\t%s\n" % (
                        processed_relation.from_token_index,
                        processed_relation.to_token_index,
                        processed_relation.relation_type,
                    )
                    file.write(write_string)
        except OSError:
            logger.error("Unable to open or create Relations .tsv file.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--annotated-filepath",
        help="Path to .jsonl file of annotations.",
        type=str,
        default="",
    )
    parser.add_argument(
        "--ner-save-filepath",
        help="Location to save the ner .tsv file",
        type=str,
        default="src/oms_sensemaking/nlp/training/data/ner_training.tsv",
    )
    parser.add_argument(
        "--relation-save-filepath",
        help="Location to save the relations .tsv file",
        type=str,
        default="src/oms_sensemaking/nlp/training/data/relations_training.tsv",
    )

    # Grabbing the arguments and saving as variables
    args = parser.parse_args()
    annotated_jsonl = args.annotated_filepath
    ner_file = args.ner_save_filepath
    relations_file = args.relation_save_filepath

    # Creating the TDP with args and running its pipeline
    processor = TrainingDataProcessor(annotated_jsonl, ner_file, relations_file)
    processor.run_pipeline()
