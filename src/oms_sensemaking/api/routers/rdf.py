import logging

from fastapi import APIRouter, HTTPException, Request, Response

from oms_sensemaking.api.schemas.rdf_format import RDFFormat
from oms_sensemaking.clients.rdf_client import RDFClient
from oms_sensemaking.core.oms_crud import OmsCrudTool

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)


@router.get("/{obj_id:path}")
@router.get("/{obj_id:path}.{format}")
def rdf_resolver(obj_id: str, request: Request, format: RDFFormat = RDFFormat.turtle) -> Response:
    """
    Resolve an object ID into its RDF representation.

    Args:
        obj_id (str): The ID of the object to resolve.
        request (Request): The request received for the RDF data.
        format (RDFFormat): RDF serialization format. Defaults to 'turtle'.

    Returns:
        Response: A FastAPI Response object containing the serialized RDF data.
    """
    request_user_dn = request.headers.get("user_dn")
    if not request_user_dn:
        raise HTTPException(status_code=401, detail="Missing user_dn.")
    oms_crud_tool = OmsCrudTool(user_dn=request_user_dn)
    rdf_client = RDFClient()
    rdfs = rdf_client.get_rdf_from_id(obj_id, format, oms_crud_tool)
    if not rdfs:
        LOGGER.error("Invalid Object. Ensure the Id is correct")
        raise HTTPException(status_code=404, detail="Object not found")
    return Response(content=rdfs, media_type="text/plain")
