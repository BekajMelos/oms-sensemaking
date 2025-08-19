import logging
import time

from fastapi import APIRouter

from oms_sensemaking.clients.instances import aac_client, corenlp_client, db_session, health_checker, oms_crud_tool
from oms_sensemaking.core.observability import record_event_processed, record_queue_processing_time

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.get("/healthcheck")
def get_healthcheck():
    """Get healthy/unhealthy report about dependencies"""
    start_time = time.time()
    system_health = {}

    system_health["oms"] = health_checker.get_oms_health(oms_crud_tool)

    system_health["aac"] = health_checker.get_aac_health(aac_client)

    system_health["nlp"] = health_checker.get_nlp_health(corenlp_client)

    system_health["db"] = health_checker.get_db_health(db_session)

    # Record health check metrics
    processing_time = time.time() - start_time
    record_queue_processing_time("health_check", processing_time)
    record_event_processed("health_check")

    return system_health
