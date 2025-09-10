import logging

from fastapi import APIRouter

from oms_sensemaking.clients.instances import aac_client, db_session, health_checker, oms_crud_tool

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.get("/healthcheck")
def get_healthcheck():
    """Get healthy/unhealthy report about dependencies"""
    system_health = {}

    system_health["oms"] = health_checker.get_oms_health(oms_crud_tool)

    system_health["aac"] = health_checker.get_aac_health(aac_client)

    system_health["db"] = health_checker.get_db_health(db_session)

    return system_health
