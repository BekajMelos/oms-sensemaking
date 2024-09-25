"""The NLP REST API."""

import dataclasses
import logging

from fastapi import APIRouter

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse
from oms_sensemaking.config import SETTINGS

# from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker
from oms_sensemaking.nlp.nlp_service import NlpService, NlpStringReader

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)


@router.post("/")
def extract_entities_and_relationships(nlp_req: NlpRequest) -> NlpResponse:
    """Run the NLP entities and relationships."""
    # Call NLP Sensemaker via the NlpService
    nlp: NlpService = NlpService()
    reader = NlpStringReader(nlp_req.text)

    # Variable host to get to CoreNLP via docker or locally (for tests)
    host = SETTINGS.corenlp_localhost if nlp_req.source_id == "sensemaking-test" else SETTINGS.corenlp_dockerhost
    findings = nlp.run_nlp(reader, nlp_req.source_id, corenlp_host=host)

    # Convert findings data to dicts for FastAPI response
    doc_rels_dict = [dataclasses.asdict(rel) for rel in findings.document_relationships]
    findings_dict = dataclasses.asdict(findings)
    findings_dict["document_relationships"] = doc_rels_dict

    return NlpResponse(acm=nlp_req.acm, source_id=nlp_req.source_id, findings=findings_dict)
