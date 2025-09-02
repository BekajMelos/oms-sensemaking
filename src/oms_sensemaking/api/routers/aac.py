"""Rest Endpoints for AAC Management"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.clients.instances import aac_client
from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/clear")
def clear_aac_cache(user_dn: Annotated[str, Depends(check_user_dn_in_whitelist)]) -> Response:
    """Clear Local AAC Cache. Available to Authorized Users Only"""
    LOGGER.info("Clearing Local AAC Cache. User %s", user_dn)
    if SETTINGS.aac_cache_enabled:
        aac_client.clear_cache()
    else:
        raise HTTPException(400, detail="Local AAC Cache not enabled. Unable to clear cache.")
    return Response(status_code=204)
