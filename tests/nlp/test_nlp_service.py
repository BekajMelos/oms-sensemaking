"""Tests for the NlpSensemakerController"""

from uuid import uuid4

from oms_sensemaking.nlp.models.submission_data import SubmissionData
from oms_sensemaking.nlp.nlp_service import NlpService

service = NlpService()
doc_id = uuid4()
sample_text = (
    "EU rejects German call to boycott British lamb. Peter Blackburn BRUSSELS 1996-08-22 "
    "The European Commission said on Thursday it disagreed with German advice to consumers "
    "to shun British lamb until scientists determine whether mad cow disease can be transmitted"
    " to sheep. Germany's representative to the European Union's veterinary committee Werner Zwingmann"
    " said on Wednesday consumers should buy sheepmeat from countries other than Britain until the "
    "scientific advice was clearer."
)
data = SubmissionData(document_id=doc_id, text=sample_text)


def test_run_nlp_sm():
    """Tests just running the business logic"""
    findings = service.run_nlp_sensemaker(data)
    assert findings.ner_entities
    assert findings.document_entity
    assert findings.ner_relationships
    assert findings.document_relationships
    assert len(findings.document_relationships) == len(findings.ner_entities)
    assert findings.document_entity.document_id == doc_id


def test_run_nlp_full_service():
    assert service.run_nlp_service(data.text)
