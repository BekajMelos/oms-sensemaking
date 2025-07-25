"""Rest Endpoints for AAC Management"""
import logging

from fastapi import APIRouter, HTTPException, Response

from oms_sensemaking.clients.instances import aac_client

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.get("/clear")
def clear_aac_cache():
    """Clear Local AAC Cache"""
    LOGGER.info("Clearing Local AAC Cache")
    aac_client.clear_cache()
    return Response(status_code=204)
