import argparse

from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.nlp.annotation_processor import AnnotationProcessor
from oms_sensemaking.nlp.corenlp_service import CoreNlpService
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.models.submission_data import SubmissionData

# TODO: Import CoreNlpService once the TDP branch is merged into main, currently had to copy/paste b/c waiting for merge


class NlpSensemaker(Sensemaker):
    """A sensemaker for analyzing text by extracting entities and the relationships between them"""

    # TODO: data will probably be a dict with a text field, and other info about the document from Controller/API
    def process_data(self, data: SubmissionData) -> EntitiesAndRelationships:
        """
        NlpSensemaker pipeline that first annotates the submitted text,
        and then processes it for entities and relationships
        """
        annotation = self.use_corenlp_service(data.text)
        processed_annotation = self.process_annotation(data, annotation)
        return processed_annotation

    def use_corenlp_service(self, document: str) -> str:
        """Accesses the CoreNlpService to annotate the text"""
        corenlp_service = CoreNlpService()
        annotated_doc = corenlp_service.annotate_document(text=document)
        return annotated_doc

    def process_annotation(self, data: SubmissionData, annotation: str) -> EntitiesAndRelationships:
        """Uses the AnnotationProcessor to get the nodes and relations from the submitted data"""
        # TODO: check what the node and relationship objects are comprised of for oms_sdk to format them w/ that info
        nodes_and_relations = AnnotationProcessor().extract_info(data, annotation)
        return nodes_and_relations


if __name__ == "__main__":
    # TODO: Will no longer need main once the full NLP SM system is implemented
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--text-filepath",
        help="Path to .txt file to be analyzed by the NLP Sensemaker.",
        type=str,
        default="src/oms_sensemaking/nlp/training/data/madcow.txt",
    )

    args = parser.parse_args()
    text_file_path = args.text_filepath

    nlp_sm = NlpSensemaker()
    with open(text_file_path, "r") as text_file:
        text = text_file.read()
    document_data = SubmissionData(document_id="MadCow", text=text)

    # This data will be used by the controller and EntityDecorator to push nodes to oms_sdk
    processed_data = nlp_sm.process_data(document_data)
    print(processed_data)  # Temporary for testing this MR
