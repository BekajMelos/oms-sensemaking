"""Rest Endpoints for AAC Management"""
import logging

from fastapi import APIRouter, HTTPException, Response

from oms_sensemaking.clients.instances import aac_client
from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/clear")
def clear_aac_cache() -> Response:
    """Clear Local AAC Cache"""
    LOGGER.info("Clearing Local AAC Cache")
    if SETTINGS.aac_cache_enabled:
        aac_client.clear_cache()
    else:
        raise HTTPException(400, detail="Local AAC Cache not enabled. Unable to clear cache.")
    return Response(status_code=204)
