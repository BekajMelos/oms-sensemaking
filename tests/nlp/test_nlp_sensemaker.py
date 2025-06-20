"""Tests for the NLP Sensemaker and Annotation Processor."""

import pytest
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.nlp.annotation_processor import AnnotationProcessor
from oms_sensemaking.nlp.models.submission_data import SubmissionData
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

from .mock_corenlp_client import MockCoreNlpClient
from .mock_responses import mock_response_long_text_str, mock_response_no_text_str

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


@pytest.fixture
def mock_corenlp_client():
    return MockCoreNlpClient({}, SETTINGS.corenlp_host)


@pytest.fixture
def nlp_sensemaker(mock_corenlp_client):
    return NlpSensemaker(mock_corenlp_client)


def test_process_data_empty_test(mock_corenlp_client, nlp_sensemaker):
    # Set mock response for this test
    mock_corenlp_client.set_response(mock_response_no_text_str)

    data = SubmissionData(document_id=sample_doc_id, text=empty_text)

    processed_data = nlp_sensemaker.process_data(data=data)

    # A document entity must be created since the text, although empty, was submitted
    assert processed_data.document_entity
    # Everything else should not exist because there was no text to process
    assert not processed_data.document_relationships
    assert not processed_data.ner_entities
    assert not processed_data.ner_relationships


def test_process_data_normal_text(mock_corenlp_client, nlp_sensemaker):
    # Set mock response for this test
    mock_corenlp_client.set_response(mock_response_long_text_str)

    data = SubmissionData(document_id=sample_doc_id, text=sample_text)

    processed_data = nlp_sensemaker.process_data(data=data)

    # There is one document relationship for every NER entity identified
    assert len(processed_data.document_relationships) == len(processed_data.ner_entities)
    # A document entity must be created since the text was submitted
    assert processed_data.document_entity


def test_use_service_empty_doc(mock_corenlp_client, nlp_sensemaker):
    # Set mock response for this test
    mock_corenlp_client.set_response(mock_response_no_text_str)

    annotation = nlp_sensemaker.use_corenlp_service(empty_text)
    # An annotation of an empty piece of text should not have any sentences
    assert not annotation


def test_use_service_normal_doc(mock_corenlp_client, nlp_sensemaker):
    # Set mock response for this test
    mock_corenlp_client.set_response(mock_response_long_text_str)

    annotation = nlp_sensemaker.use_corenlp_service(sample_text)
    # An annotation of a document should contain sentences
    assert annotation


def test_annotation_processor(mock_corenlp_client, nlp_sensemaker):
    # Set mock response for this test
    mock_corenlp_client.set_response(mock_response_long_text_str)

    data = SubmissionData(sample_doc_id, sample_text)

    annotation = nlp_sensemaker.use_corenlp_service(sample_text)
    ann_processor = AnnotationProcessor()
    sentences = ann_processor.find_sentences(annotation)
    assert len(sentences) == 1
    ents, rels = [], []
    for sentence in sentences:
        tokens = ann_processor.find_tokens(sentence)
        ents += ann_processor.find_entities(sentence, tokens)
        ents = ann_processor.consolidate_entities(ents)
        rels += ann_processor.find_relationships(sentence, tokens)
    all_ents_and_rels = ann_processor.relate_to_document(data, ents, rels)

    # Every entity in the annotation should be typed, multi-token ents should be consolidated
    for ent in ents:
        assert ent["type"] != "0"
        assert "B-" not in ent["type"]
        assert "I-" not in ent["type"]
        assert "E-" not in ent["type"]

    # Every relation in the annotation and its entities must have a type
    for rel in rels:
        assert rel["type"] != "_NR"
        for ent in rel["entities"]:
            assert ent["type"] != "0"

    # There is one document relationship for every NER entity identified
    assert len(all_ents_and_rels.document_relationships) == len(all_ents_and_rels.ner_entities)
    # Every document relation created must have the attribute type Document_Contains_Entity
    for doc_rel in all_ents_and_rels.document_relationships:
        assert doc_rel.type == "Document_Contains_Entity"
    # Every document relation created must have the attribute document_id matching the original document's id
    assert all_ents_and_rels.document_entity.document_id == sample_doc_id
    # Every document relation created must have the attribute entity_type matching the original document's id
    assert all_ents_and_rels.document_entity.entity_type == "DOCUMENT"
