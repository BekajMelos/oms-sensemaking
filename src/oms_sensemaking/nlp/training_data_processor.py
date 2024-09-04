import argparse
import json
import logging

from collections_extended import RangeMap
from models.doccano_result import DoccanoResult
from stanza.server import CoreNLPClient

from oms_sensemaking.nlp.models.doccano_entity import DoccanoEntity
from oms_sensemaking.nlp.models.doccano_relation import DoccanoRelation
from oms_sensemaking.nlp.models.processed_relation import ProcessedRelation
from oms_sensemaking.nlp.models.processed_result import ProcessedResult
from oms_sensemaking.nlp.models.token_reference import TokenReference

# TODO: get props from config file
CUSTOM_PROPS = {
    "annotators": "tokenize, pos, lemma, depparse",
}
corenlp_client = CoreNLPClient(properties=CUSTOM_PROPS, timeout=60000, memory="16G")

logger = logging.getLogger(__name__)


class TrainingDataProcessor:
    def __init__(self, annotated_filepath: str, ner_save_filepath: str, relation_save_filepath: str):
        self.annotated_filepath = annotated_filepath
        self.ner_save_filepath = ner_save_filepath
        self.relation_save_filepath = relation_save_filepath
        self.properties = ""

    def run_pipeline(self):
        # TODO: include logger info while running pipeline
        doccano_result = self.load_jsonl_file()
        processed_doccano_result = self.process_doccano_result(doccano_result)
        self.write_ner_result(processed_doccano_result, self.ner_save_filepath)
        self.write_relation_result(processed_doccano_result, self.relation_save_filepath)
        return None

    def load_jsonl_file(self) -> DoccanoResult:
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
        This func builds the DoccanoResult data type
        """
        # Tokenize the entities and relations
        text = doccano_result.text
        processed_result = ProcessedResult(doccano_result.id)

        # Go through text, annotate with client, and get sentences
        with corenlp_client:  # The client is used here only for annotation purposes, no NER or relation extraction yet
            annotation = corenlp_client.annotate(text)
        sentences = annotation.sentence  # grab the sentences from the annotation

        # Loop through sentences and make tokens for doccano token map
        global_token_index = 0
        doc_token_range_map = RangeMap()  # maps ranges of char offsets to TokenReferences
        for sentence in sentences:
            for token in sentence.token:
                start_offset = token.beginChar
                end_offset = token.endChar
                pos_tag = token.pos
                token_reference = TokenReference(
                    token.originalText, global_token_index, start_offset, end_offset, "0", pos_tag
                )
                global_token_index += 1

                # add new token to range map
                doc_token_range_map.set(token_reference, start_offset, end_offset)
        processed_result.doc_token_map = doc_token_range_map

        # Build the map of entity ID to token
        entity_token_map = {}
        for doccano_entity in doccano_result.entities:
            # print(doccano_entity)
            # Get list of tokens in the offset range
            # From Java implementation: '-2' was required on the end to prevent the inclusion of trailing punctuation
            # TODO: Figure out how to properly index into RangeMap
            sub_map = doc_token_range_map.get_range(doccano_entity.start_offset, doccano_entity.end_offset - 2)
            token_list = []
            for key in sub_map:
                print(sub_map[key])
                token_list.append(sub_map[key])
            # token_list = [doc_token_range_map.get(doccano_entity.start_offset, doccano_entity.end_offset - 2)]
            # When there are multiple entities per label, need the result of the following:
            token_count = len(token_list)
            for i in range(token_count):
                current_token = token_list[i]
                token_key = current_token.start_offset, current_token.end_offset
                current_label = doccano_entity.label
                # TODO: make sure this part is working properly b/c none are appearing in document
                if i == 0:
                    label_prefix = "B-"
                elif i == token_count - 1:
                    label_prefix = "E-"
                else:
                    label_prefix = "I-"

                # Updating the label if there are multiple tokens for this label
                updated_label = current_label if token_count == 1 else label_prefix + current_label

                # Adding the token with the updated label back to the RangeMap
                current_token.label = updated_label
                doc_token_range_map.delete(token_key[0], token_key[1])
                doc_token_range_map.set(current_token, token_key[0], token_key[1])

                # Update the dict of tokens by id
                entity_token_map[doccano_entity.id] = current_token

        processed_result.entity_token_ref = entity_token_map

        # Go through relations and grab necessary info to add to processed result
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

        processed_result.processed_relation_set = processed_relation_set

        return processed_result

    def write_ner_result(self, processed_result: ProcessedResult, ner_filepath: str):
        try:
            with open(ner_filepath, "w") as file:
                token_refs = processed_result.doc_token_map

                # Writing the NER label information for each entity to the file
                for ref in token_refs.values():
                    write_string = "%s\t%s\n" % (ref.token, ref.label)
                    file.write(write_string)

        except OSError:  # TODO: find the best error to raise
            logger.error("Unable to open or create NER file.")
        return None

    def write_relation_result(self, processed_result: ProcessedResult, relation_filepath: str):
        try:
            with open(relation_filepath, "w") as file:
                token_refs = processed_result.doc_token_map

                # writing the relation details for each token
                for ref in token_refs.values():
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

                file.write("\n")

                # writing summary of existing relations at the bottom of the file
                for processed_relation in processed_result.processed_relation_set:
                    write_string = "%s\t%s\t%s\n" % (
                        processed_relation.from_token_index,
                        processed_relation.to_token_index,
                        processed_relation.relation_type,
                    )
                    file.write(write_string)
        except OSError:  # TODO: find the best error to raise
            logger.error("Unable to open or create Relations file.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--annotated-filepath",
        help="Path to .jsonl file of annotations.",
        type=str,
        default="./training/russiaukraine_test.jsonl",
    )
    parser.add_argument(
        "--ner-save-filepath",
        help="Location to save the ner .tsv file",
        type=str,
        default="src/oms_sensemaking/nlp/training/ner_test.tsv",
    )
    parser.add_argument(
        "--relation-save-filepath",
        help="Location to save the relations .tsv file",
        type=str,
        default="src/oms_sensemaking/nlp/training/relations_test.tsv",
    )

    args = parser.parse_args()
    annotated_jsonl = args.annotated_filepath
    ner_file = args.ner_save_filepath
    relations_file = args.relation_save_filepath

    processor = TrainingDataProcessor(annotated_jsonl, ner_file, relations_file)
    processor.run_pipeline()
