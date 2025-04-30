import logging

from fastapi import APIRouter, HTTPException
from pydantic import UUID4

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.clients.rdf_client import RDFClient

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)
rdf_client = RDFClient()

@router.get('/resolver/{obj_id}')
@router.get('/resolver/{obj_id}.{format}')
def rdf_resolver(obj_id: UUID4, format: str = "turtle"):
    rdfs = rdf_client.get_rdf_from_id(obj_id, format, oms_crud_tool)
    if not rdfs:
        LOGGER.error("Invalid Object. Ensure the Id is correct")
        raise HTTPException(status_code=404, detail="Object not found")
    return rdfs
