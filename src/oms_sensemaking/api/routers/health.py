import logging

from fastapi import APIRouter
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.input_types import (
    NodeQuery,
    PageParams,
)
from sqlalchemy import text

from oms_sensemaking.clients import corenlp_client, db_session, oms_crud_tool
from oms_sensemaking.core import acm as aac_client
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()
healthy = "healthy"
unhealthy = "Unable to communicate with"


@router.get("/healthcheck")
def get_healthcheck():
    """Get healthy/unhealthy report about dependencies"""
    system_health = {}

    system_health["oms"] = get_oms_health(oms_crud_tool)

    system_health["aac"] = get_aac_health(aac_client)

    system_health["nlp"] = get_nlp_health(corenlp_client)

    system_health["db"] = get_db_health()
    return system_health


def get_oms_health(oms_crud_tool: OmsCrudTool):
    LOGGER.debug("Checking OMS health")
    try:
        query = NodeQuery(pageParams=PageParams(pageSize=1))
        oms_crud_tool.get_nodes(query)
        return healthy
    except Exception as e:
        LOGGER.error(repr(e))
        return f"{unhealthy} OMS"


def get_db_health():
    LOGGER.debug("Checking DB health")
    try:
        with db_session() as db:
            db.execute(text("SELECT 1"))
            return healthy
    except Exception as e:
        LOGGER.error(repr(e))
        return f"{unhealthy} DB"


def get_aac_health(aac_service):
    LOGGER.debug("Checking AAC Service health")
    try:
        aac_service.get_acm_rollup([DEFAULT_ACM])
        return healthy
    except Exception as e:
        LOGGER.error(repr(e))
        return f"{unhealthy} AAC Service"


def get_nlp_health(corenlp_client: CoreNlpClient):
    LOGGER.debug("Checking NLP Service health")
    try:
        corenlp_client.annotate_document_xml("the quick brown fox jumped over the lazy dog")
        return healthy
    except Exception as e:
        LOGGER.error(repr(e))
        return f"{unhealthy} NLP Service"
