"""The NLP REST API."""

import logging
import time

from fastapi import APIRouter, HTTPException

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse
from oms_sensemaking.clients.instances import corenlp_client
from oms_sensemaking.core.observability import record_event_failed, record_event_processed, record_queue_processing_time
from oms_sensemaking.nlp.nlp_reader import NlpStringReader
from oms_sensemaking.nlp.nlp_service import NlpService

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)


@router.post("/")
def extract_entities_and_relationships(nlp_req: NlpRequest) -> NlpResponse:
    """Run the NLP entities and relationships."""
    start_time = time.time()
    LOGGER.info(f"NLP API Request: {nlp_req}")

    try:
        # Call NLP Sensemaker via the NlpService to get findings (eventually will also submit to OMS)
        nlp: NlpService = NlpService()

        # Validate the source before running the pipeline
        if not nlp.validate_source(nlp_req.source_id):
            LOGGER.error("Source ID is invalid. Please make sure the source exists.")
            record_event_failed("nlp_processing")
            raise HTTPException(status_code=404, detail="Invalid source")
        else:
            # Run the pipeline
            reader = NlpStringReader(nlp_req.text)
            findings = nlp.run_service(request=nlp_req, nlp_reader=reader, corenlp_client=corenlp_client)

            # Record successful processing metrics
            processing_time = time.time() - start_time
            record_queue_processing_time("nlp_processing", processing_time)
            record_event_processed("nlp_processing")

            return NlpResponse(acm=nlp_req.acm, source_id=nlp_req.source_id, findings=findings)

    except Exception as e:
        # Record failed processing metrics
        record_event_failed("nlp_processing")
        LOGGER.error(f"NLP processing failed: {e}")
        raise
