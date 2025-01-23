"""The NLP REST API."""

import logging

from fastapi import APIRouter, HTTPException

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse
from oms_sensemaking.clients import corenlp_client
from oms_sensemaking.nlp.nlp_reader import NlpStringReader
from oms_sensemaking.nlp.nlp_service import NlpService

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)


@router.post("/")
def extract_entities_and_relationships(nlp_req: NlpRequest) -> NlpResponse:
    """Run the NLP entities and relationships."""
    LOGGER.info(f"NLP API Request: {nlp_req}")

    # Call NLP Sensemaker via the NlpService to get findings (eventually will also submit to OMS)
    nlp: NlpService = NlpService()

    # Validate the source before running the pipeline
    if not nlp.validate_source(nlp_req.source_id):
        LOGGER.error("Source ID is invalid. Please make sure the source exists.")
        raise HTTPException(status_code=404, detail="Invalid source")
    else:
        # Run the pipeline
        reader = NlpStringReader(nlp_req.text)
        findings = nlp.run_service(request=nlp_req, nlp_reader=reader, corenlp_client=corenlp_client)

        return NlpResponse(acm=nlp_req.acm, source_id=nlp_req.source_id, findings=findings)
