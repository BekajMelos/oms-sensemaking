"""Tests for the NLP Sensemaker and Annotation Processor."""

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.nlp.annotation_processor import AnnotationProcessor
from oms_sensemaking.nlp.models.submission_data import SubmissionData
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

empty_text = ""
sample_text = (
    "EU rejects German call to boycott British lamb. Peter Blackburn BRUSSELS 1996-08-22 "
    "The European Commission said on Thursday it disagreed with German advice to consumers "
    "to shun British lamb until scientists determine whether mad cow disease can be transmitted"
    " to sheep. Germany's representative to the European Union's veterinary committee Werner Zwingmann"
    " said on Wednesday consumers should buy sheepmeat from countries other than Britain until the "
    "scientific advice was clearer."
)
sample_doc_id = "MadCow"
nlp_sensemaker = NlpSensemaker(corenlp_host=SETTINGS.corenlp_localhost)


def test_process_data_empty_test():
    data = SubmissionData(document_id=sample_doc_id, text=empty_text)

    processed_data = nlp_sensemaker.process_data(data=data)

    # A document entity must be created since the text, although empty, was submitted
    assert processed_data.document_entity
    # Everything else should not exist because there was no text to process
    assert not processed_data.document_relationships
    assert not processed_data.ner_entities
    assert not processed_data.ner_relationships


def test_process_data_normal_text():
    data = SubmissionData(document_id=sample_doc_id, text=sample_text)

    processed_data = nlp_sensemaker.process_data(data=data)

    # There is one document relationship for every NER entity identified
    assert len(processed_data.document_relationships) == len(processed_data.ner_entities)
    # A document entity must be created since the text was submitted
    assert processed_data.document_entity


def test_use_service_empty_doc():
    annotation = nlp_sensemaker.use_corenlp_service(empty_text)
    # An annotation of an empty piece of text should not have any sentences
    assert not annotation


def test_use_service_normal_doc():
    annotation = nlp_sensemaker.use_corenlp_service(sample_text)
    # An annotation of a document should contain sentences
    assert annotation


def test_annotation_processor():
    data = SubmissionData(sample_doc_id, sample_text)

    annotation = nlp_sensemaker.use_corenlp_service(sample_text)
    ann_processor = AnnotationProcessor()
    ents = ann_processor.find_entities(annotation)
    rels = ann_processor.find_relationships(annotation)
    all_ents_and_rels = ann_processor.relate_to_document(data, ents, rels)

    # Every entity in the annotation must have been extracted
    for sentence in annotation:
        if "MachineReading" in sentence and sentence["MachineReading"]["entities"]:
            # Loop through each of the entities in the annotation
            for entity in sentence["MachineReading"]["entities"]["entity"]:
                if entity["#text"] != "O":
                    assert entity in ents
        # Every relation in the annotation must have been extracted
        if "MachineReading" in sentence and sentence["MachineReading"]["relations"]:
            # TODO: Verify formatting
            for relation in sentence["MachineReading"]["relations"]["relation"]:
                if relation["#text"] != "_NR":
                    assert relation in rels
    # Every relation added must not have type _NR
    for relation in rels:
        assert relation["#text"] != "_NR"

    # There is one document relationship for every NER entity identified
    assert len(all_ents_and_rels.document_relationships) == len(all_ents_and_rels.ner_entities)
    # Every document relation created must have the attribute type Document_Contains_Entity
    for doc_rel in all_ents_and_rels.document_relationships:
        assert doc_rel.type == "Document_Contains_Entity"
    # Every document relation created must have the attribute document_id matching the original document's id
    assert all_ents_and_rels.document_entity.document_id == sample_doc_id
    # Every document relation created must have the attribute entity_type matching the original document's id
    assert all_ents_and_rels.document_entity.entity_type == "DOCUMENT"
