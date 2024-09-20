from fastapi import APIRouter

from oms_sensemaking.api.schemas.nlp import AnalyzeTextResponse
from oms_sensemaking.models.nlp import TextSubmission
from oms_sensemaking.nlp.nlp_service import NlpService

router: APIRouter = APIRouter()


@router.post("/ner", response_model=AnalyzeTextResponse, response_model_exclude_none=True, status_code=200)
def analyze_text(submission: TextSubmission):
    nlp: NlpService = NlpService()
    nlp.run_nlp_service(submission.text)
    return AnalyzeTextResponse(success=True)
