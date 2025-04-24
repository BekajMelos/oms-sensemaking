import logging

from fastapi import APIRouter, HTTPException
from pydantic import UUID4

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.clients.rdf_client import RDFClient

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)
rdf_client = RDFClient()

@router.get('/resolver/{obj_id}')
def rdf_resolver(obj_id: UUID4):
    node = rdf_client.get_rdf_from_id(obj_id, oms_crud_tool)
    if not node:
        raise HTTPException(status_code=404, detail="Object not found")
    return node
