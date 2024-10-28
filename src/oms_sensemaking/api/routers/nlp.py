"""The NLP REST API."""

import logging

from fastapi import APIRouter, HTTPException

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient
from oms_sensemaking.nlp.nlp_service import NlpService, NlpStringReader

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)

corenlp_client = CoreNlpClient(props={}, hostname=SETTINGS.corenlp_host)


@router.post("/")
def extract_entities_and_relationships(nlp_req: NlpRequest) -> NlpResponse:
    """Run the NLP entities and relationships."""

    # Call NLP Sensemaker via the NlpService to get findings (eventually will also submit to OMS)
    nlp: NlpService = NlpService()

    # Validate the source before running the pipeline
    if not nlp.validate_source(nlp_req.source_id):
        raise HTTPException(status_code=404, detail="Invalid source")
    else:
        # Run the pipeline
        reader = NlpStringReader(nlp_req.text)
        findings = nlp.run_service(
            acm=nlp_req.acm, nlp_reader=reader, source_id=nlp_req.source_id, corenlp_client=corenlp_client
        )

        return NlpResponse(acm=nlp_req.acm, source_id=nlp_req.source_id, findings=findings)
