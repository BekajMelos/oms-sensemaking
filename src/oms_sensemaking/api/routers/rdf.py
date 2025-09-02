"""RDF Endpoints"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from oms_sensemaking.api.routers.utils import require_user_dn
from oms_sensemaking.api.schemas.rdf_format import RDFFormat
from oms_sensemaking.clients.rdf_client import RDFClient
from oms_sensemaking.core.oms_crud import OmsCrudTool

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)

USER_DN = "user_dn"


@router.get("/{obj_id:path}")
@router.get("/{obj_id:path}.{format}")
def rdf_resolver(
    user_dn: Annotated[str, Depends(require_user_dn)], obj_id: str, format: RDFFormat = RDFFormat.turtle
) -> Response:
    """
    Resolve an object ID into its RDF representation.

    Args:
        obj_id (str): The ID of the object to resolve.
        request (Request): The request received for the RDF data.
        format (RDFFormat): RDF serialization format. Defaults to 'turtle'.

    Returns:
        Response: A FastAPI Response object containing the serialized RDF data.
    """

    oms_crud_tool = OmsCrudTool(user_dn=user_dn)
    rdf_client = RDFClient()
    rdfs = rdf_client.get_rdf_from_id(obj_id, format, oms_crud_tool)
    if not rdfs:
        LOGGER.error("Invalid Object. Ensure the Id is correct")
        raise HTTPException(status_code=404, detail="Object not found")
    return Response(content=rdfs, media_type="text/plain")
