from fastapi import APIRouter
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import start_controller_and_wait
from oms_sensemaking.nlp.controllers import NlpApiReceiver, NlpSensemakerController

router: APIRouter = APIRouter()


# TODO: Add response model
@router.post("/ner", status_code=200)
def analyze_text(text: str):
    nlp: NlpSensemakerController = NlpSensemakerController(NlpApiReceiver(text, DEFAULT_ACM, SETTINGS.user_dn))
    start_controller_and_wait(nlp)
    return {"status": "OK"}
