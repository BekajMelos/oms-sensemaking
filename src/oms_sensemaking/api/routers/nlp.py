"""The NLP REST API."""

from fastapi import APIRouter

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse
from oms_sensemaking.config import SETTINGS

# from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker
from oms_sensemaking.nlp.nlp_service import NlpService, NlpStringReader

router: APIRouter = APIRouter()


@router.post("/")
def extract_entities_and_relationships(nlp_req: NlpRequest) -> NlpResponse:
    """Run the NLP entities and relationships."""
    # TODO: call the sensemaker with the input data
    # results = NlpSensemaker.execute()
    nlp: NlpService = NlpService()
    reader = NlpStringReader(nlp_req.text)

    # Variable host due to testing needs vs docker needs
    host = SETTINGS.corenlp_localhost if nlp_req.source_id == "sensemaking-test" else SETTINGS.corenlp_dockerhost
    nlp.run_nlp(reader, nlp_req.source_id, corenlp_host=host)
    # TODO: determine what part of the results should be returned to the caller
    return NlpResponse(acm=nlp_req.acm)
