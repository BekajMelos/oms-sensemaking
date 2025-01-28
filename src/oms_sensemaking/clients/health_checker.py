import logging

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.input_types import (
    NodeQuery,
    PageParams,
)
from sqlalchemy import text

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient

LOGGER: logging.Logger = logging.getLogger(__name__)


class HealthChecker:
    """Get health status of dependencies"""

    _healthy = "healthy"
    _unhealthy = "Unable to communicate with"

    def get_oms_health(self, oms_crud_tool: OmsCrudTool):
        LOGGER.debug("Checking OMS health")
        try:
            query = NodeQuery(pageParams=PageParams(pageSize=1))
            oms_crud_tool.get_nodes(query)
            return self._healthy
        except Exception as e:
            LOGGER.error(repr(e))
            return f"{self._unhealthy} OMS"

    def get_db_health(self, db_session):
        LOGGER.debug("Checking DB health")
        try:
            with db_session() as db:
                db.execute(text("SELECT 1"))
                return self._healthy
        except Exception as e:
            LOGGER.error(repr(e))
            return f"{self._unhealthy} DB Service"

    def get_aac_health(self, aac_service: AacClient):
        LOGGER.debug("Checking AAC Service health")
        try:
            aac_service.get_acm_rollup([DEFAULT_ACM])
            return self._healthy
        except Exception as e:
            LOGGER.error(repr(e))
            return f"{self._unhealthy} AAC Service"

    def get_nlp_health(self, corenlp_client: CoreNlpClient):
        LOGGER.debug("Checking NLP Service health")
        try:
            corenlp_client.annotate_document_xml("the quick brown fox jumped over the lazy dog")
            return self._healthy
        except Exception as e:
            LOGGER.error(repr(e))
            return f"{self._unhealthy} NLP Service"
