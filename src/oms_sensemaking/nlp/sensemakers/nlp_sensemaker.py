"""Natural Language Processing (NLP) Sensemaker."""

import argparse

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.nlp.annotation_processor import AnnotationProcessor
from oms_sensemaking.nlp.corenlp_service import CoreNlpService
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.models.submission_data import SubmissionData


class NlpSensemaker(Sensemaker):
    """
    A sensemaker for analyzing text by extracting entities and the relationships between them.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial NLP algorithm implementation.

    """

    def __init__(self, corenlp_host: str = SETTINGS.corenlp_dockerhost) -> None:
        """Create a new instance of NlpSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.corenlp_host = corenlp_host

    def process_data(self, data: SubmissionData) -> EntitiesAndRelationships:
        """
        Run the data through an NLP pipeline.

        The NLP pipeline will first annotate the submitted text, and then
        process it for entities and relationships.
        """
        annotation = self.use_corenlp_service(data.text)
        processed_annotation = self.process_annotation(data, annotation)
        return processed_annotation

    def use_corenlp_service(self, document: str) -> dict:
        """Access the CoreNlpService to annotate text."""
        corenlp_service = CoreNlpService(props={}, host=self.corenlp_host)
        annotated_doc = corenlp_service.annotate_document(text=document)
        return annotated_doc

    def process_annotation(self, data: SubmissionData, annotation: dict) -> EntitiesAndRelationships:
        """Use the AnnotationProcessor to get the nodes and relations from the submitted data."""
        nodes_and_relations = AnnotationProcessor().extract_info(data, annotation)
        return nodes_and_relations


if __name__ == "__main__":
    # TODO: Later - Will no longer need main once the full NLP SM system is implemented
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--text-filepath",
        help="Path to .txt file to be analyzed by the NLP Sensemaker.",
        type=str,
        default="src/oms_sensemaking/nlp/training/data/madcow.txt",
    )

    args = parser.parse_args()
    text_file_path = args.text_filepath

    nlp_sm = NlpSensemaker(corenlp_host=SETTINGS.corenlp_localhost)
    with open(text_file_path, "r") as text_file:
        text = text_file.read()
    document_data = SubmissionData(document_id="MadCow", text=text)

    # This data will be used by the controller and EntityDecorator to push nodes to oms_sdk
    processed_data = nlp_sm.process_data(document_data)
    print(processed_data)  # Temporary for testing this MR
